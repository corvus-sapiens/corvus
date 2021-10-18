"""Functions that ease the pain of working with databases (primarily PostgreSQL)."""

import logging
from collections import namedtuple
from typing import List, Dict, Any

import pandas as pd
import sqlalchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from corvus.cmd import get_cmd_output


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
QueryCriterion = namedtuple("QueryCriterion", ("column", "value"))
ORMPrimaryKey = namedtuple("ORMPrimaryKey", ("attribute", "value"))


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
def get_pg_entity_names(engine: sqlalchemy.engine.Engine, entity: str) -> List[str]:
    if entity == "table":
        pg_column = "tablename"
        pg_table = "pg_tables"
    elif entity == "view":
        pg_column = "viewname"
        pg_table = "pg_views"
    else:
        raise ValueError("Argument 'entity' is neither 'table' nor 'view'")

    select = sqlalchemy.text(f"""
        SELECT "{pg_column}"
        FROM "pg_catalog"."{pg_table}"
        WHERE "schemaname" <> 'pg_catalog'
            AND "schemaname" <> 'information_schema';
    """)

    with engine.connect() as conn:
        return pd.read_sql(select, con=conn).squeeze().tolist()


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
## TODO: rework as a normal Docker SDK call
def backup_db(service_name: str, logger: logging.LoggerAdapter) -> None:
    logger.info(f"Running PostgreSQL backup via a Docker Compose service: {service_name}")

    cmd = f"docker exec {service_name} /backup.sh"
    logger.debug(f"CMD: '{cmd}'")

    output = get_cmd_output(cmd)
    if output["rc"]:
        logger.error(f"(docker-compose:{service_name}) [stderr] {output['stderr']}")

    last_message = [line.strip() for line in output["stdout"]][-1]

    logger.debug(f"(docker-compose:{service_name}) [stdout] {last_message}")


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def row_exists(table_name: str, criterion: QueryCriterion, engine: sqlalchemy.engine.Engine, logger: logging.LoggerAdapter) -> bool:
    try:
        query = sqlalchemy.text(f"""SELECT exists(SELECT 1 FROM "{table_name}" WHERE "{criterion.column}" = :value);""")
        with engine.connect() as conn:
            return bool(
                conn.execute(query, value=criterion.value).fetchone()[0]
            )
    except Exception as error:
        logger.error(f"({criterion}) Error accessing database: {error}")
        return False


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_primary_key(table_name: str, engine: sqlalchemy.engine.Engine) -> str:
    ## https://wiki.postgresql.org/wiki/Retrieve_primary_key_columns
    query = f"""
SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
FROM pg_index i
JOIN pg_attribute a ON a.attrelid = i.indrelid
    AND a.attnum = ANY (i.indkey)
WHERE i.indrelid = '"{table_name}"'::regclass
    AND i.indisprimary;
    """

    with engine.connect() as conn:
        return conn.execute(query).fetchone()[0]


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_pg_engine(path_pgpass: str, logger: logging.LoggerAdapter) -> sqlalchemy.engine.Engine:
    db_settings = parse_pgpass(path=path_pgpass, logger=logger)
    params = {k.strip(): v for k, v in db_settings.copy().items() if k != "db_password"}
    logger.debug(f"DB connection parameters: {params}")
    db_url = "postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}".format(**db_settings)
    return sqlalchemy.create_engine(db_url, client_encoding="utf8")


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_sqlite_engine(db_path: str, logger: logging.LoggerAdapter) -> sqlalchemy.engine.Engine:
    db_url = f"sqlite:///{db_path}"
    logger.debug(f"Attempting to connect using database URL: '{db_url}'")
    return sqlalchemy.create_engine(db_url)


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def parse_pgpass(path: str, logger: logging.LoggerAdapter) -> dict:
    """
    Return a dict of SQLAlchemy settings for the psycopg2 driver.
    :param path: where to look for the .pgpass file
    :param logger: a logging.LoggerAdapter instance
    :return: a dictionary of credentials
    """
    try:
        with open(path, "r", encoding="ascii") as file:
            db_host, db_port, db_name, db_user, db_password = file.read().strip().split(":")
        return {
            "db_host": db_host,
            "db_port": db_port,
            "db_name": db_name,
            "db_user": db_user,
            "db_password": db_password,
        }
    except Exception as error:
        logger.error(f"Failed to parse the .pgpass file ({str(error)}): {path}")
        return {}


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def upsert_orm(orm_cls, attributes: Dict[str, Any], engine: sqlalchemy.engine.Engine, pkey: ORMPrimaryKey, logger: logging.LoggerAdapter) -> Any:
    """
    Emulate an UPSERT (UPdate/inSERT) operation for a row in an ORM-defined SQL table

    :param orm_cls: class object, extending SQLAlchemy Base to represent a SQL table
    :param attributes: property_name->value mapping to be setattr'ed on an instance of the ``orm_cls`` class
    :param engine: a SQLAlchemy engine (connection factory)
    :param pkey: a namedtuple that stores a non-composite PrimaryKey for the SQL table, represented by ``orm_cls``
    :param logger: an configured logging.Logger object
    :returns: None
    """

    logger.debug(f"Received an ORM object: '{orm_cls.__tablename__}' ({orm_cls.__name__})")
    with engine.connect() as conn:
        session = Session(conn)

        logger.debug(f"Making an ORM-relayed SELECT query with a primary key criterion: '{pkey.attribute}:{pkey.value}' ...")
        instance = (
            session
            .query(orm_cls)
            .filter(getattr(orm_cls, pkey.attribute) == pkey.value)
            .first()
        )

        if not instance:
            logger.debug(f"Entry not found, will run an INSERT operation: '{pkey.attribute}:{pkey.value}'")
            instance = orm_cls(**{pkey.attribute: pkey.value})
        else:
            logger.debug(f"Entry discovered, will run an UPDATE operation: '{pkey.attribute}:{pkey.value}'")

        logger.debug(f"Will upsert the following fields: {attributes}")
        try:
            for key in attributes:
                setattr(instance, key, attributes[key])

            session.add(instance)
            session.commit()
        except (IntegrityError, AttributeError) as error:
            logger.error(f"Encountered an error during an ORM upsert ({repr(error)}): '{pkey.attribute}:{pkey.value}'")
            raise

        session.refresh(instance)
        returned_pkey = getattr(instance, pkey.attribute)
        logger.debug(f"Returned primary key ('{pkey.attribute}'): {returned_pkey}")

    return returned_pkey
