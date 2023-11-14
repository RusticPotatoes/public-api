import logging
import time

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncResult, AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import Select

from src.app.views.input.feedback import FeedbackInput
from src.core.database.models.feedback import PredictionFeedback as dbFeedback
from src.core.database.models.player import Player as dbPlayer
from src.core.database.models.prediction import Prediction as dbPrediction
from src.core.database.models.report import Report as dbReport
from src.core.fastapi.dependencies.to_jagex_name import to_jagex_name

logger = logging.getLogger(__name__)


class Player:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_jagex_name(self, feedback: FeedbackInput):
        formatted_name = to_jagex_name(feedback.player_name)
        # name should be 1-13 characters
        if (
            formatted_name is not None
            and len(formatted_name) > 0
            and len(formatted_name) < 14
        ):
            feedback.player_name = formatted_name
            return feedback
        else:
            return None

    async def parse_feedback(self, feedback: FeedbackInput):
        """
        Validate feedback data
        """

        data = self._to_jagex_name(feedback)
        if not data:
            logger.warning("invalid name")
            return None

        return data

    async def get_report_score(self, player_names: tuple[str]):
        """
        Retrieve Kill Count (KC) data for a list of player names.

        Args:
            player_names (list[str]): A list of player names for which KC data is requested.

        Returns:
            tuple: A tuple of dictionaries containing KC data for each player name. Each dictionary
                includes the following keys:
                - "count": The distinct count of reported players.
                - "possible_ban": Whether the player has a possible ban (True or False).
                - "confirmed_ban": Whether the player has a confirmed ban (True or False).
                - "confirmed_player": Whether the player is confirmed as a valid player (True or False).
                - "manual_detect": Wheter the detection was manual (True or False)
        """
        # Create aliases for the tables
        reporting_player: dbPlayer = aliased(dbPlayer, name="reporting_player")
        reported_player: dbPlayer = aliased(dbPlayer, name="reported_player")

        query: Select = select(
            [
                func.count(func.distinct(reported_player.id)).label("count"),
                reported_player.possible_ban,
                reported_player.confirmed_ban,
                reported_player.confirmed_player,
                dbReport.manual_detect,
            ]
        )
        query = query.select_from(dbReport)
        query = query.join(
            reporting_player, dbReport.reportingID == reporting_player.id
        )
        query = query.join(reported_player, dbReport.reportedID == reported_player.id)
        query = query.where(dbPlayer.name.in_(player_names))
        query = query.group_by(
            reported_player.possible_ban,
            reported_player.confirmed_ban,
            reported_player.confirmed_player,
            dbReport.manual_detect,
        )
        async with self.session:
            result: AsyncResult = await self.session.execute(query)
            await self.session.commit()
        return tuple(result.mappings())

    async def get_feedback_score(self, player_names: list[str]):
        # dbFeedback
        feedback_voter: dbPlayer = aliased(dbPlayer, name="feedback_voter")
        feedback_subject: dbPlayer = aliased(dbPlayer, name="feedback_subject")

        query: Select = select(
            [
                func.count(func.distinct(feedback_subject.id)).label("count"),
                feedback_subject.possible_ban,
                feedback_subject.confirmed_ban,
                feedback_subject.confirmed_player,
                dbFeedback.vote,
            ]
        )
        query = query.select_from(dbFeedback)
        query = query.join(feedback_voter, dbFeedback.voter_id == feedback_voter.id)
        query = query.join(
            feedback_subject, dbFeedback.subject_id == feedback_subject.id
        )
        query = query.where(feedback_voter.name.in_(player_names))
        query = query.group_by(
            feedback_subject.possible_ban,
            feedback_subject.confirmed_ban,
            feedback_subject.confirmed_player,
            dbFeedback.vote,
        )

        async with self.session:
            result: AsyncResult = await self.session.execute(query)
            await self.session.commit()
        return tuple(result.mappings())

    async def get_prediction(self, player_names: list[str]):
        query: Select = select(dbPrediction)
        query = query.select_from(dbPrediction)
        query = query.where(dbPrediction.name.in_(player_names))
        async with self.session:
            result: AsyncResult = await self.session.execute(query)
            result = result.scalars().all()
        return jsonable_encoder(result)

    async def post_feedback(self, feedback: FeedbackInput):
        async with self.session:
            # check if the player name is anonymoususer
            if feedback.player_name == "anonymoususer":
                # check if the player exists
                anonymous_user_query = select(dbPlayer).where(
                    dbPlayer.name == "anonymoususer"
                )
                anonymous_user_insert = dbPlayer(name="anonymoususer")
                anonymous_result: AsyncResult = await self.session.execute(anonymous_user_query)
                # create anonymoususer if it does not exist
                if not anonymous_result.scalar():
                    anonymous_result: AsyncResult = await self.session.execute(anonymous_user_insert)

                    await self.session.commit()

            # check if the player exists
            player = await self.session.execute(
                select(dbPlayer).where(dbPlayer.name == feedback.player_name)
            )

            # create player if it does not exist
            if not player.scalar():
                self.session.add(dbPlayer(name=feedback.player_name))
                await self.session.commit()

            # if the subject exists create a new feedback entry else create a new player and feedback entry
            subject = await self.session.execute(
                select(dbPlayer).where(dbPlayer.name == feedback.subject_id)
            )

            # no clue what else?

            self.session.add(dbFeedback(**feedback.dict()))
            await self.session.commit()
        return
