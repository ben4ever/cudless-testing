CUDless testing
===============

Recipe for efficient testing with `pytest <http://pytest.org/>`_ for
`flask-sqlalchemy <http://flask-sqlalchemy.pocoo.org/>`_ based
applications.

FAQ
---

* What is this?

  I had two visions for efficient testing:

  * I want to write test suites which can utilize a database but never have to
    actually write (i.e. commit) rows to it.
  * I don't want to setup/initialize the database with its default table rows
    (e.g. a table of all country names or a table of available color names) for
    every single test run. Instead, I want to initialize the database once and
    then run all my tests on top of that.

  This recipe is an effort in accomplishing these two goals.
  
* Can you briefly explain how this recipe works?

  * All the testing happens within a main transaction which is rolled back at
    the end of testing.
  * I use nested subtransactions to still be able to commit and rollback freely
    in my application code.
  * The database initialization is performed in a lower nesting level than the
    one in which the individual tests are run in. Therefore, after each
    individual test, all changes performed by that test can be just rolled back
    without the initialization tasks being rolled back as well (hence the
    database initialization is isolated from the tests).

* How do I use this for my own project?

  The most important file is ``tests/conftest.py``. This is where all the heavy
  lifting is done. I suggest that you copy this file to your own ``tests``
  directory and then read through it and modify it as necessary.

  ``tests/test_example.py`` is an example of what your tests could look like.

  ``cudless_testing/__init__.py`` is an example of what your application
  code could look like.

* Which database dialects are supported?

  I have tested it with SQLite only but there is nothing dialect specific in the
  code which would prevent you from using a different dialect. Keep in mind
  though that support for SAVEPOINTs is required.

* How is this recipe different to `SQLAlchemy's recipe in the docs
  <http://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites>`_?

  While SQLAlchemy's recipe works great, I think it's a bit inconvenient to bind
  a ``Session`` to a ``Connection`` which is already in a transactional state,
  when using the ``flask-sqlalchemy`` library.

* Why CUDless?

  Since this recipe is utilizing a database without creating, updating or
  deleting any rows in a committed transaction, we use the acronym `CRUD
  <https://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`_ but without
  the R for read. And because we never actually commit any CUD, our approach is
  "CUDless".
