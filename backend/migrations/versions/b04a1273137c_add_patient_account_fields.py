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
    # Connect existing patient records to an optional login account.
    # Nullable is intentional because existing demo patients do not
    # have patient login accounts.
    op.add_column(
        "patients",
        sa.Column(
            "user_id",
            sa.String(length=36),
            nullable=True,
        ),
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