from typing import List, Any, TypeVar, Generic
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Base

# Declare a type variable T with a constraint that it is a subclass of Base
T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, session: AsyncSession):
        # Find a record by ID
        logger.info(f"Searching for {cls.model.__name__} with ID: {data_id}")
        try:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Record with ID {data_id} found.")
            else:
                logger.info(f"Record with ID {data_id} not found.")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Error while searching for record with ID {data_id}: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        # Find one record by filters
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Searching for one {cls.model.__name__} record with filters: {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Record found with filters: {filter_dict}")
            else:
                logger.info(f"Record not found with filters: {filter_dict}")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Error while searching for record with filters {filter_dict}: {e}")
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None):
        # Find all records matching the filters
        if filters:
            filter_dict = filters.model_dump(exclude_unset=True)
        else:
            filter_dict = {}
        logger.info(f"Searching for all {cls.model.__name__} records with filters: {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            records = result.scalars().all()
            logger.info(f"Found {len(records)} records.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Error while searching for all records with filters {filter_dict}: {e}")
            raise

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        # Add a single record
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Adding a {cls.model.__name__} record with parameters: {values_dict}")
        new_instance = cls.model(**values_dict)
        session.add(new_instance)
        try:
            await session.flush()
            logger.info(f"{cls.model.__name__} record added successfully.")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error while adding record: {e}")
            raise e
        return new_instance

    @classmethod
    async def add_many(cls, session: AsyncSession, instances: List[BaseModel]):
        # Add multiple records
        values_list = [item.model_dump(exclude_unset=True) for item in instances]
        logger.info(f"Adding multiple {cls.model.__name__} records. Count: {len(values_list)}")
        new_instances = [cls.model(**values) for values in values_list]
        session.add_all(new_instances)
        try:
            await session.flush()
            logger.info(f"Successfully added {len(new_instances)} records.")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error while adding multiple records: {e}")
            raise e
        return new_instances

    @classmethod
    async def update(cls, session: AsyncSession, filters: BaseModel, values: BaseModel):
        # Update records matching the filters
        filter_dict = filters.model_dump(exclude_unset=True)
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Updating {cls.model.__name__} records with filter: {filter_dict} and parameters: {values_dict}")
        query = (
            sqlalchemy_update(cls.model)
            .where(*[getattr(cls.model, k) == v for k, v in filter_dict.items()])
            .values(**values_dict)
            .execution_options(synchronize_session="fetch")
        )
        try:
            result = await session.execute(query)
            await session.flush()
            logger.info(f"Updated {result.rowcount} records.")
            return result.rowcount
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error while updating records: {e}")
            raise e

    @classmethod
    async def delete(cls, session: AsyncSession, filters: BaseModel):
        # Delete records matching the filters
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Deleting {cls.model.__name__} records with filter: {filter_dict}")
        if not filter_dict:
            logger.error("At least one filter is required for deletion.")
            raise ValueError("At least one filter is required for deletion.")

        query = sqlalchemy_delete(cls.model).filter_by(**filter_dict)
        try:
            result = await session.execute(query)
            await session.flush()
            logger.info(f"Deleted {result.rowcount} records.")
            return result.rowcount
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error while deleting records: {e}")
            raise e

    @classmethod
    async def count(cls, session: AsyncSession, filters: BaseModel):
        # Count the number of records matching the filters
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Counting {cls.model.__name__} records with filter: {filter_dict}")
        try:
            query = select(func.count(cls.model.id)).filter_by(**filter_dict)
            result = await session.execute(query)
            count = result.scalar()
            logger.info(f"Found {count} records.")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error while counting records: {e}")
            raise

    @classmethod
    async def paginate(cls, session: AsyncSession, page: int = 1, page_size: int = 10, filters: BaseModel = None):
        # Paginate records
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(
            f"Paginating {cls.model.__name__} records with filter: {filter_dict}, page: {page}, page size: {page_size}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
            records = result.scalars().all()
            logger.info(f"Found {len(records)} records on page {page}.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Error while paginating records: {e}")
            raise

    @classmethod
    async def find_by_ids(cls, session: AsyncSession, ids: List[int]) -> List[Any]:
        """Find multiple records by a list of IDs"""
        logger.info(f"Searching for {cls.model.__name__} records by list of IDs: {ids}")
        try:
            query = select(cls.model).filter(cls.model.id.in_(ids))
            result = await session.execute(query)
            records = result.scalars().all()
            logger.info(f"Found {len(records)} records by list of IDs.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Error while searching for records by list of IDs: {e}")
            raise

    @classmethod
    async def upsert(cls, session: AsyncSession, unique_fields: List[str], values: BaseModel):
        """Create or update a record"""
        values_dict = values.model_dump(exclude_unset=True)
        filter_dict = {field: values_dict[field] for field in unique_fields if field in values_dict}

        logger.info(f"Upsert for {cls.model.__name__}")
        try:
            existing = await cls.find_one_or_none(session, BaseModel.construct(**filter_dict))
            if existing:
                # Update existing record
                for key, value in values_dict.items():
                    setattr(existing, key, value)
                await session.flush()
                logger.info(f"Updated existing {cls.model.__name__} record")
                return existing
            else:
                # Create a new record
                new_instance = cls.model(**values_dict)
                session.add(new_instance)
                await session.flush()
                logger.info(f"Created new {cls.model.__name__} record")
                return new_instance
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error during upsert: {e}")
            raise

    @classmethod
    async def bulk_update(cls, session: AsyncSession, records: List[BaseModel]) -> int:
        """Bulk update records"""
        logger.info(f"Bulk updating {cls.model.__name__} records")
        try:
            updated_count = 0
            for record in records:
                record_dict = record.model_dump(exclude_unset=True)
                if 'id' not in record_dict:
                    continue

                update_data = {k: v for k, v in record_dict.items() if k != 'id'}
                stmt = (
                    sqlalchemy_update(cls.model)
                    .filter_by(id=record_dict['id'])
                    .values(**update_data)
                )
                result = await session.execute(stmt)
                updated_count += result.rowcount

            await session.flush()
            logger.info(f"Updated {updated_count} records")
            return updated_count
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error during bulk update: {e}")
            raise
