"""Add timestamp to Comment model

Revision ID: e0a6bdf837b2
Revises: 43084d9ec738
Create Date: 2023-08-31 23:55:43.606670

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0a6bdf837b2'
down_revision = '43084d9ec738'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('timestamp', sa.DateTime(), nullable=True))
        batch_op.alter_column('text',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.Text(),
               existing_nullable=False)
        batch_op.drop_column('date_posted')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_posted', sa.DATETIME(), nullable=True))
        batch_op.alter_column('text',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=500),
               existing_nullable=False)
        batch_op.drop_column('timestamp')

    # ### end Alembic commands ###
