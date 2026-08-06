"""add vehicle_tyres table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-06

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    existing_tables = sa.inspect(bind).get_table_names()
    if 'vehicle_tyres' not in existing_tables:
        op.create_table(
            'vehicle_tyres',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('vehicle_id', sa.Integer(), nullable=False),
            sa.Column('make', sa.String(length=100), nullable=True),
            sa.Column('tyre_number', sa.String(length=50), nullable=False),
            sa.Column('installed_date', sa.Date(), nullable=True),
            sa.Column('installed_km', sa.Integer(), nullable=True),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('vehicle_id', 'tyre_number', name='uq_vehicle_tyre_number'),
        )


def downgrade():
    op.drop_table('vehicle_tyres')
