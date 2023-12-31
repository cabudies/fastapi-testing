"""init

Revision ID: 3680eaf990b6
Revises: 
Create Date: 2023-12-27 02:29:18.918611

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '3680eaf990b6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('products',
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_products_created_on'), 'products', ['created_on'], unique=False)
    op.create_index(op.f('ix_products_description'), 'products', ['description'], unique=False)
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_table('products_variants',
    sa.Column('sku', sa.VARCHAR(), nullable=True),
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sku')
    )
    op.create_index(op.f('ix_products_variants_created_on'), 'products_variants', ['created_on'], unique=False)
    op.create_index(op.f('ix_products_variants_id'), 'products_variants', ['id'], unique=False)
    op.create_index(op.f('ix_products_variants_product_id'), 'products_variants', ['product_id'], unique=False)
    op.create_table('price_list',
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_variant_id', sa.Integer(), nullable=True),
    sa.Column('min_quantity', sa.Integer(), nullable=False),
    sa.Column('max_quantity', sa.Integer(), nullable=False),
    sa.Column('special_price', sa.Float(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_variant_id'], ['products_variants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('min_quantity', 'max_quantity', 'product_variant_id', name='special_price_based_on_min_and_max_quantity')
    )
    op.create_index(op.f('ix_price_list_created_on'), 'price_list', ['created_on'], unique=False)
    op.create_index(op.f('ix_price_list_id'), 'price_list', ['id'], unique=False)
    op.create_index(op.f('ix_price_list_max_quantity'), 'price_list', ['max_quantity'], unique=False)
    op.create_index(op.f('ix_price_list_min_quantity'), 'price_list', ['min_quantity'], unique=False)
    op.create_index(op.f('ix_price_list_product_variant_id'), 'price_list', ['product_variant_id'], unique=False)
    op.create_index(op.f('ix_price_list_special_price'), 'price_list', ['special_price'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_price_list_special_price'), table_name='price_list')
    op.drop_index(op.f('ix_price_list_product_variant_id'), table_name='price_list')
    op.drop_index(op.f('ix_price_list_min_quantity'), table_name='price_list')
    op.drop_index(op.f('ix_price_list_max_quantity'), table_name='price_list')
    op.drop_index(op.f('ix_price_list_id'), table_name='price_list')
    op.drop_index(op.f('ix_price_list_created_on'), table_name='price_list')
    op.drop_table('price_list')
    op.drop_index(op.f('ix_products_variants_product_id'), table_name='products_variants')
    op.drop_index(op.f('ix_products_variants_id'), table_name='products_variants')
    op.drop_index(op.f('ix_products_variants_created_on'), table_name='products_variants')
    op.drop_table('products_variants')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_index(op.f('ix_products_description'), table_name='products')
    op.drop_index(op.f('ix_products_created_on'), table_name='products')
    op.drop_table('products')
    # ### end Alembic commands ###
