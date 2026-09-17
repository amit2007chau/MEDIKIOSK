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

    # Get the columns that already exist in the patients table.
    columns = {
        column["name"]
        for column in inspector.get_columns("patients")
    }

    # ---------------------------------------------------------
    # user_id
    # ---------------------------------------------------------
    # The initial migration may already create this column.
    # Add it only if it is actually missing.
    if "user_id" not in columns:
        op.add_column(
            "patients",
            sa.Column(
                "user_id",
                sa.String(length=36),
                nullable=True,
            ),
        )

    # ---------------------------------------------------------
    # address
    # ---------------------------------------------------------
    # Add only if the column does not already exist.
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

    # ---------------------------------------------------------
    # preferred_language
    # ---------------------------------------------------------
    # Add only if the column does not already exist.
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

    # ---------------------------------------------------------
    # user_id unique index
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # user_id foreign key
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Remove temporary server defaults.
    # ---------------------------------------------------------
    # Only remove them when these columns are present.
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


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("patients")
    }

    # Remove foreign key if it exists.
    foreign_keys = inspector.get_foreign_keys("patients")

    for fk in foreign_keys:
        if (
            fk.get("referred_table") == "users"
            and "user_id" in fk.get("constrained_columns", [])
        ):
            constraint_name = fk.get("name")

            if constraint_name:
                op.drop_constraint(
                    constraint_name,
                    "patients",
                    type_="foreignkey",
                )

    # Remove index if it exists.
    existing_indexes = {
        index["name"]
        for index in inspector.get_indexes("patients")
    }

    if "ix_patients_user_id" in existing_indexes:
        op.drop_index(
            "ix_patients_user_id",
            table_name="patients",
        )

    # Remove columns only if they exist.
    if "preferred_language" in columns:
        op.drop_column(
            "patients",
            "preferred_language",
        )

    if "address" in columns:
        op.drop_column(
            "patients",
            "address",
        )

    if "user_id" in columns:
        op.drop_column(
            "patients",
            "user_id",
        )