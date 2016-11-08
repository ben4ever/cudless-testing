from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
sa = SQLAlchemy(app)


class User(sa.Model):
    __tablename__ = 'users'

    id_ = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


def init_db():
    sa.create_all()
    sa.session.add(User(name='default user'))
    sa.session.commit()


@app.route('/default')
def get_default_user_name():
    return (
        sa.session.query(User.name)
            .filter(User.name == 'default user')
            .scalar()
        )
