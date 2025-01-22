from server import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    twitch_id = db.Column(db.String())
    auth_token = db.Column(db.String())
    refresh_token = db.Column(db.String())
    refresh_expires = db.Column(db.Datetime())

    def __init__(self, twitch_id, auth_token, refresh_token):
        self.twitch_id = twitch_id
        self.auth_token = auth_token
        self.refresh_token = refresh_token

    def __repr__(self):
        return '<id {}>'.format(self.id)
