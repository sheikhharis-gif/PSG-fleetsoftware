"""Add cargo_id to trips

Revision ID: 76ee7e932fab
Revises: 
Create Date: 2026-06-08 15:36:24.010217

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76ee7e932fab'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add the column first
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cargo_id', sa.Integer(), nullable=True))
    
    # Add foreign key with a proper name
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_trips_cargo_id',  # ← Name added here
            'cargo_manifests',
            ['cargo_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.drop_constraint('fk_trips_cargo_id', type_='foreignkey')  # ← Name added here
        batch_op.drop_column('cargo_id')