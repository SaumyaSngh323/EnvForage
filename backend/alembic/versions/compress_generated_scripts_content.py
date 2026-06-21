"""compress generated script content

Revision ID: compress_generated_scripts
Revises: f113b99acf31
Create Date: 2026-06-21

"""

from alembic import op
import sqlalchemy as sa


revision = "compress_generated_scripts"
down_revision = "f113b99acf31"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "generated_scripts",
        "content",
        existing_type=sa.Text(),
        type_=sa.LargeBinary(),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "generated_scripts",
        "content",
        existing_type=sa.LargeBinary(),
        type_=sa.Text(),
        existing_nullable=False,
    )