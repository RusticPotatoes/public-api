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
                func.coalesce(dbReport.manual_detect, 0).label("manual_detect"),
            ]
        )
        query = query.select_from(dbReport)
        query = query.join(
            reporting_player, dbReport.reportingID == reporting_player.id
        )
        query = query.join(reported_player, dbReport.reportedID == reported_player.id)
        query = query.where(reporting_player.name.in_(player_names))
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

    async def get_player_id(self, player_name: str):
        user_query = select(dbPlayer).where(dbPlayer.name == player_name)
        async with self.session:
            user_result: AsyncResult = await self.session.execute(user_query)
            player = user_result.scalar_one_or_none()
            return player.id if player else None

    async def add_player(self, player_name: str):
        async with self.session:
            logger.info(f"creating new feedback player {player_name}")
            new_player = dbPlayer(name=player_name)
            self.session.add(new_player)
            await self.session.commit()
            await self.session.refresh(new_player)
            player_id = new_player.id
            return player_id

    async def post_feedback(self, feedback: FeedbackInput, player_id: int):
        async with self.session:
            # check subject_id exists in dbPlayer
            subject_query = select(dbPlayer).where(dbPlayer.id == feedback.subject_id)
            subject_result: AsyncResult = await self.session.execute(subject_query)
            if not subject_result.scalar_one_or_none():
                logger.warning("invalid subject_id")
                return None

            # if the subject exists create a new feedback entry
            if subject_result.scalar_one_or_none():
                logger.info(f"creating new feedback for {feedback.subject_id}")
                new_feedback = dbFeedback(
                    voter_id=player_id,
                    subject_id=feedback.subject_id,
                    vote=feedback.vote,
                    prediction=feedback.prediction,
                    confidence=feedback.confidence,
                    feedback_text=feedback.feedback_text,
                    proposed_label=feedback.proposed_label,
                )
                self.session.add(new_feedback)
                await self.session.commit()
                await self.session.refresh(new_feedback)
                subject_feedback_result = new_feedback

            if not subject_feedback_result:
                logger.error("invalid feedback given")
                return None

        return
