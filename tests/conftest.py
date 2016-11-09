import sqlite3

import pytest
from sqlalchemy import event
from flask_sqlalchemy import SignallingSession

import cudless_testing
from cudless_testing import app, sa

FUNC_MAP = {}


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='session', autouse=True)
def setup():
    app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'SQLALCHEMY_ECHO': True,
            }
        )
    event.listen(sa.engine, 'connect', _do_connect)
    event.listen(sa.engine, 'begin', _do_begin)
    with app.test_request_context():
        # Create nesting to prevent any commits/rollbacks within the DB
        # setup to apply onto our top level transaction.
        sa.session.begin_nested()
        # TODO. Change SignallingSession to sa.session once
        # https://github.com/mitsuhiko/flask-sqlalchemy/pull/364 is in a
        # release.
        event.listen(
            SignallingSession,
            'after_transaction_end',
            _get_restart_savepoint_func(2)
            )

        cudless_testing.init_db()

        # TODO. Change SignallingSession to sa.session once
        # https://github.com/mitsuhiko/flask-sqlalchemy/pull/364 is in a
        # release.
        event.remove(
            SignallingSession,
            'after_transaction_end',
            _get_restart_savepoint_func(2)
            )
        # End our nesting for DB setup.
        sa.session.commit()

        yield

        # Our final rollback so that we end our test session without
        # leaving any DML traces in the DB.
        sa.session.rollback()


@pytest.fixture(autouse=True)
def nest_for_test():
    # Nesting level 1 to rollback current test.
    sa.session.begin_nested()

    # Nesting level 2 to handle any commits/rollbacks within a test.
    sa.session.begin_nested()
    # TODO. Change SignallingSession to sa.session once
    # https://github.com/mitsuhiko/flask-sqlalchemy/pull/364 is in a
    # release.
    event.listen(
        SignallingSession,
        'after_transaction_end',
        _get_restart_savepoint_func(3)
        )

    yield

    # TODO. Change SignallingSession to sa.session once
    # https://github.com/mitsuhiko/flask-sqlalchemy/pull/364 is in a
    # release.
    event.remove(
        SignallingSession,
        'after_transaction_end',
        _get_restart_savepoint_func(3)
        )
    # Rollback nesting level 2.
    sa.session.rollback()

    # Rollback nesting level 1.
    sa.session.rollback()


def _get_restart_savepoint_func(parent_levels):
    def restart_savepoint(session, transaction):
        node = transaction
        # Ensure we're at the proper nesting level.
        for i in range(parent_levels):
            node = node.parent
        if node is None:
            session.expire_all()
            session.begin_nested()

    # We can't generate a function on the fly on every function call
    # since SQLAlchemy's `event.remove` will look for the same function
    # object which was previously added by `event.listen`. Hence we use
    # a dict to save each generated function only once, and recall it
    # from the dict later when `event.remove` is called.
    return FUNC_MAP.setdefault(parent_levels, restart_savepoint)


def _do_connect(dbapi_connection, connection_record):
    '''See `this explanation`__ what this is needed for.

    __ http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
    '''
    if isinstance(dbapi_connection, sqlite3.Connection):
        # Disable pysqlite's emitting of the BEGIN statement entirely.
        # Also stops it from emitting COMMIT before any DDL.
        dbapi_connection.isolation_level = None


def _do_begin(conn):
    '''See `this explanation`__ what this is needed for.

    __ http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
    '''
    if isinstance(conn.connection.connection, sqlite3.Connection):
        # Emit our own BEGIN.
        conn.execute('BEGIN')
