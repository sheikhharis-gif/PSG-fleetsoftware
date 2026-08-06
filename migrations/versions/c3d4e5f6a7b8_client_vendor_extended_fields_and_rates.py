"""client/vendor extended fields, ClientType registry, Client Rates revision log, DedicatedRate

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-06

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    existing_tables = sa.inspect(bind).get_table_names()

    # --- Client Types registry ---
    if 'client_types' not in existing_tables:
        op.create_table(
            'client_types',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )

    # --- Clients: add new columns ---
    existing_client_cols = {c['name'] for c in sa.inspect(bind).get_columns('clients')}
    with op.batch_alter_table('clients', schema=None) as batch_op:
        if 'client_type_id' not in existing_client_cols:
            batch_op.add_column(sa.Column('client_type_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_clients_client_type_id', 'client_types', ['client_type_id'], ['id'])
        if 'poc1_name' not in existing_client_cols:
            batch_op.add_column(sa.Column('poc1_name', sa.String(length=100), nullable=True))
        if 'poc1_phone' not in existing_client_cols:
            batch_op.add_column(sa.Column('poc1_phone', sa.String(length=20), nullable=True))
        if 'poc1_email' not in existing_client_cols:
            batch_op.add_column(sa.Column('poc1_email', sa.String(length=120), nullable=True))
        if 'poc2_name' not in existing_client_cols:
            batch_op.add_column(sa.Column('poc2_name', sa.String(length=100), nullable=True))
        if 'poc2_phone' not in existing_client_cols:
            batch_op.add_column(sa.Column('poc2_phone', sa.String(length=20), nullable=True))
        if 'poc2_email' not in existing_client_cols:
            batch_op.add_column(sa.Column('poc2_email', sa.String(length=120), nullable=True))
        if 'stn' not in existing_client_cols:
            batch_op.add_column(sa.Column('stn', sa.String(length=30), nullable=True))
        if 'term_of_service' not in existing_client_cols:
            batch_op.add_column(sa.Column('term_of_service', sa.String(length=100), nullable=True))
        if 'billing_period' not in existing_client_cols:
            batch_op.add_column(sa.Column('billing_period', sa.String(length=50), nullable=True))
        if 'billing_company' not in existing_client_cols:
            batch_op.add_column(sa.Column('billing_company', sa.String(length=150), nullable=True))

    # migrate old single poc -> poc1_name, then drop the old column
    existing_client_cols = {c['name'] for c in sa.inspect(bind).get_columns('clients')}
    if 'poc' in existing_client_cols:
        op.execute("UPDATE clients SET poc1_name = poc WHERE poc1_name IS NULL")
        with op.batch_alter_table('clients', schema=None) as batch_op:
            batch_op.drop_column('poc')

    # --- Vendors: add new columns ---
    existing_vendor_cols = {c['name'] for c in sa.inspect(bind).get_columns('vendors')}
    with op.batch_alter_table('vendors', schema=None) as batch_op:
        if 'poc1_name' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('poc1_name', sa.String(length=100), nullable=True))
        if 'poc1_phone' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('poc1_phone', sa.String(length=20), nullable=True))
        if 'poc1_email' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('poc1_email', sa.String(length=120), nullable=True))
        if 'poc2_name' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('poc2_name', sa.String(length=100), nullable=True))
        if 'poc2_phone' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('poc2_phone', sa.String(length=20), nullable=True))
        if 'poc2_email' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('poc2_email', sa.String(length=120), nullable=True))
        if 'stn' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('stn', sa.String(length=30), nullable=True))
        if 'term_of_service' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('term_of_service', sa.String(length=100), nullable=True))
        if 'billing_period' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('billing_period', sa.String(length=50), nullable=True))
        if 'is_active' not in existing_vendor_cols:
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()))

    # migrate old poc/phone -> poc1_name/poc1_phone, then drop old columns
    existing_vendor_cols = {c['name'] for c in sa.inspect(bind).get_columns('vendors')}
    if 'poc' in existing_vendor_cols:
        op.execute("UPDATE vendors SET poc1_name = poc WHERE poc1_name IS NULL")
    if 'phone' in existing_vendor_cols:
        op.execute("UPDATE vendors SET poc1_phone = phone WHERE poc1_phone IS NULL")
    with op.batch_alter_table('vendors', schema=None) as batch_op:
        if 'poc' in existing_vendor_cols:
            batch_op.drop_column('poc')
        if 'phone' in existing_vendor_cols:
            batch_op.drop_column('phone')
        batch_op.alter_column('name', existing_type=sa.String(length=100), type_=sa.String(length=150))
        batch_op.alter_column('address', existing_type=sa.Text(), nullable=True)

    # --- Client Rates: rebuild as fuel-price revision log ---
    # The old table has a "rate"/"fuel_price" pair (single rate per client+route,
    # enforced by an unnamed UNIQUE(client_id, route_id) constraint) which is
    # fundamentally incompatible with the new revision-log shape (many dated
    # rows per client+route). Nothing has ever been entered into this table in
    # production (Trip mode was a bare stub until now), so instead of fighting
    # SQLite's unnamed-constraint reflection in batch mode, just drop and
    # recreate it fresh.
    existing_rate_cols = {c['name'] for c in sa.inspect(bind).get_columns('client_rates')}
    if 'current_fuel_price' not in existing_rate_cols:
        op.drop_table('client_rates')
        op.create_table(
            'client_rates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('client_id', sa.Integer(), nullable=False),
            sa.Column('route_id', sa.Integer(), nullable=False),
            sa.Column('current_fuel_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('current_rate', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('effective_percent', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('rate_subject_to_revision', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('updated_fuel_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('fuel_price_change_percent', sa.Numeric(precision=6, scale=2), nullable=True),
            sa.Column('rate_adjustment', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('updated_trip_cost', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('effective_date', sa.Date(), nullable=False),
            sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
            sa.ForeignKeyConstraint(['route_id'], ['routes.id']),
            sa.PrimaryKeyConstraint('id'),
        )

    # --- Dedicated Rates ---
    if 'dedicated_rates' not in existing_tables:
        op.create_table(
            'dedicated_rates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('client_id', sa.Integer(), nullable=False),
            sa.Column('vehicle_id', sa.Integer(), nullable=False),
            sa.Column('fixed_cost', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('month', sa.Date(), nullable=False),
            sa.Column('fuel_avg', sa.Numeric(precision=6, scale=2), nullable=False),
            sa.Column('fuel_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('variable_cost', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('route_id', sa.Integer(), nullable=False),
            sa.Column('distance_mode', sa.String(length=10), nullable=True),
            sa.Column('distance_km', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('effective_date', sa.Date(), nullable=False),
            sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
            sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id']),
            sa.ForeignKeyConstraint(['route_id'], ['routes.id']),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    op.drop_table('dedicated_rates')
    op.drop_table('client_rates')
    op.create_table(
        'client_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('fuel_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'route_id'),
    )
    with op.batch_alter_table('vendors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('poc', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch_op.drop_column('poc1_name')
        batch_op.drop_column('poc1_phone')
        batch_op.drop_column('poc1_email')
        batch_op.drop_column('poc2_name')
        batch_op.drop_column('poc2_phone')
        batch_op.drop_column('poc2_email')
        batch_op.drop_column('stn')
        batch_op.drop_column('term_of_service')
        batch_op.drop_column('billing_period')
        batch_op.drop_column('is_active')
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('poc', sa.String(length=100), nullable=True))
        batch_op.drop_constraint('fk_clients_client_type_id', type_='foreignkey')
        batch_op.drop_column('client_type_id')
        batch_op.drop_column('poc1_name')
        batch_op.drop_column('poc1_phone')
        batch_op.drop_column('poc1_email')
        batch_op.drop_column('poc2_name')
        batch_op.drop_column('poc2_phone')
        batch_op.drop_column('poc2_email')
        batch_op.drop_column('stn')
        batch_op.drop_column('term_of_service')
        batch_op.drop_column('billing_period')
        batch_op.drop_column('billing_company')
    op.drop_table('client_types')
