from db import url_object
# from models import User, Poll, PollOption, PollSelection
from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
# from sqlalchemy.sql import func

engine = create_engine(url_object, echo=True)
Base.metadata.create_all(engine)

with Session(engine) as session:
    # ######### Add seed data here #########
    # bbbthunda = User(id=123, twitch_id=321, twitch_username="BBBThunda")
    # active_poll = Poll(
    #     id=234,
    #     target="BBBThunda",
    #     creator_twitch_id=321,
    #     description="Which game should we play next?",
    #     start=func.now(),
    #     end=func.now(),
    #     status=1,
    #     options=[
    #         PollOption(
    #             id=345, poll_id=234, number=1,
    #             text="The Legend of Zelda: Tears of the Kingdom"
    #         ),
    #         PollOption(
    #             id=346, poll_id=234, number=2,
    #             text="Crypt of the Necrodancer"
    #         ),
    #         PollOption(
    #             id=347, poll_id=234, number=3,
    #             text="Dark Souls: Remastered"
    #         ),
    #     ],
    # )
    # session.add_all([bbbthunda, active_poll])
    # session.commit()
    pass
