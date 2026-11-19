from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '872b89f09c40'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('genres',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('publishers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)

    op.create_table('shelves',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('shelves', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_shelves_owner_id'), ['owner_id'], unique=False)

    op.create_table('books',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('author', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('pages', sa.Integer(), nullable=True),
    sa.Column('is_favorite', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('genre_id', sa.Integer(), nullable=True),
    sa.Column('publisher_id', sa.Integer(), nullable=True),
    sa.Column('shelf_id', sa.Integer(), nullable=True),
    sa.CheckConstraint("status IN ('want', 'reading', 'read')", name='ck_books_status'),
    sa.CheckConstraint('pages IS NULL OR pages > 0', name='ck_books_pages'),
    sa.CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='ck_books_rating'),
    sa.ForeignKeyConstraint(['genre_id'], ['genres.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['publisher_id'], ['publishers.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['shelf_id'], ['shelves.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_books_owner_id'), ['owner_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_books_title'), ['title'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_books_title'))
        batch_op.drop_index(batch_op.f('ix_books_owner_id'))

    op.drop_table('books')
    with op.batch_alter_table('shelves', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_shelves_owner_id'))

    op.drop_table('shelves')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))

    op.drop_table('users')
    op.drop_table('publishers')
    op.drop_table('genres')
