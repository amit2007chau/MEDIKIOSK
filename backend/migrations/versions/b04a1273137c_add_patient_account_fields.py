"""add patient account fields

Revision ID: b04a1273137c
Revises: 0001_initial
Create Date: 
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b04a1273137c"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("patients")
    }

    # user_id may already exist in the initial schema.
    # Add it only when it is actually missing.
    if "user_id" not in columns:
        op.add_column(
            "patients",
            sa.Column(
                "user_id",
                sa.String(length=36),
                nullable=True,
            ),
        )

    # Add address only if it does not already exist.
    if "address" not in columns:
        op.add_column(
            "patients",
            sa.Column(
                "address",
                sa.String(length=500),
                nullable=False,
                server_default="",
            ),
        )

    # Add preferred_language only if it does not already exist.
    if "preferred_language" not in columns:
        op.add_column(
            "patients",
            sa.Column(
                "preferred_language",
                sa.String(length=20),
                nullable=False,
                server_default="en",
            ),
        )

    # Refresh schema information after possible column additions.
    inspector = sa.inspect(bind)

    # Create the unique user_id index only if it is missing.
    existing_indexes = {
        index["name"]
        for index in inspector.get_indexes("patients")
    }

    if "ix_patients_user_id" not in existing_indexes:
        op.create_index(
            "ix_patients_user_id",
            "patients",
            ["user_id"],
            unique=True,
        )

    # Create the users(id) -> patients(user_id) relationship only if
    # an equivalent foreign key does not already exist.
    inspector = sa.inspect(bind)
    foreign_keys = inspector.get_foreign_keys("patients")

    user_id_fk_exists = any(
        fk.get("referred_table") == "users"
        and "user_id" in fk.get("constrained_columns", [])
        for fk in foreign_keys
    )

    if not user_id_fk_exists:
        op.create_foreign_key(
            "fk_patients_user_id_users",
            "patients",
            "users",
            ["user_id"],
            ["id"],
        )

    # Remove temporary database-level defaults.
    if "address" in columns:
        op.alter_column(
            "patients",
            "address",
            server_default=None,
        )

    if "preferred_language" in columns:
        op.alter_column(
            "patients",
            "preferred_language",
            server_default=None,
        )

    # Existing patients need valid values when these columns are added.
    # Temporary server defaults allow the migration to succeed safely.
    op.add_column(
        "patients",
        sa.Column(
            "address",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
    )

    op.add_column(
        "patients",
        sa.Column(
            "preferred_language",
            sa.String(length=20),
            nullable=False,
            server_default="en",
        ),
    )

    op.create_index(
        "ix_patients_user_id",
        "patients",
        ["user_id"],
        unique=True,
    )

    op.create_foreign_key(
        None,
        "patients",
        "users",
        ["user_id"],
        ["id"],
    )

    # Remove the temporary database-level defaults.
    # The SQLAlchemy model still provides application-level defaults.
    op.alter_column(
        "patients",
        "address",
        server_default=None,
    )

    op.alter_column(
        "patients",
        "preferred_language",
        server_default=None,
    )


def downgrade():
    op.drop_constraint(
        None,
        "patients",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_patients_user_id",
        table_name="patients",
    )

    op.drop_column(
        "patients",
        "preferred_language",
    )

    op.drop_column(
        "patients",
        "address",
    )

    op.drop_column(
        "patients",
        "user_id",
    )