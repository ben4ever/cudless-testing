from cudless_testing import sa, User


def test_default_user():
    assert User.query.count() == 1


def test_add_user():
    sa.session.add(User(name='foo'))
    sa.session.commit()
    assert User.query.count() == 2


def test_get_default_user_name(client):
    assert client.get('/default').get_data() == b'default user'
