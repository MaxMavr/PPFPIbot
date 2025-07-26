from aiogram.types import Message

from phrases import PHRASES_RU
from DB.tables.queries import QueriesTable
from DB.tables.users import UsersTable
from utils import format_list
from bot import command_arguments, pages
from bot.routers import AdminRouter, BaseRouter
from utils.music_yandex import get_song_artist_title_by_song_id
from DB.files.admin_song import upd_admin_song
from utils.links import take_yandex_song_link


router = AdminRouter()


@router.command('users', 'таблица со всеми пользователями')  # /users
async def _(message: Message):
    await pages.get_users(message.from_user.id)


@router.command('getcmds', 'список всех доступных команд')  # /getcmds
async def _(message: Message):
    commands_text = PHRASES_RU.title.commands
    admin_commands = '\n'.join(str(command) for command in BaseRouter.available_commands if command.is_admin)
    if admin_commands:
        commands_text += PHRASES_RU.subtitle.admin_commands + admin_commands
    user_commands = '\n'.join(str(command) for command in BaseRouter.available_commands if not command.is_admin)
    if user_commands:
        commands_text += PHRASES_RU.subtitle.user_commands + user_commands
    await message.answer(commands_text)


@router.command('updasong', 'обновить песню «Что слушает админ?»', 'ссылка на Яндекс Музыку')  # /updasong
@command_arguments.yandex_link
async def _(message: Message, yandex_link):
    album_id, song_id = take_yandex_song_link(yandex_link)
    song_title, artist_title = await get_song_artist_title_by_song_id(song_id)
    upd_admin_song([song_title, artist_title, song_id, album_id])
    await message.answer(PHRASES_RU.success.save_admin_song)


@router.command('ban', 'заблокировать пользователя по ID', 'user_id')  # /ban
@command_arguments.user_id
async def _(message: Message, user_id):
    if message.from_user.id == int(user_id):
        await message.answer(PHRASES_RU.error.ban_yourself)
        return
    with UsersTable() as user_db:
        if user_db.set_ban_status(user_id, message.from_user.id, True):
            await message.answer(PHRASES_RU.replace('success.banned', user_id=user_id))
        else:
            await message.answer(PHRASES_RU.error.db)


@router.command('unban', 'разблокировать пользователя по ID', 'user_id')  # /unban
@command_arguments.user_id
async def _(message: Message, user_id):
    with UsersTable() as user_db:
        if user_db.set_ban_status(user_id, message.from_user.id, False):
            await message.answer(PHRASES_RU.replace('success.unbanned', user_id=user_id))
        else:
            await message.answer(PHRASES_RU.error.db)


@router.command('promote', 'повысить уровень доступа', 'user_id')  # /promote
@command_arguments.user_id
async def _(message: Message, user_id):
    with UsersTable() as users_db:
        if users_db.set_admin(user_id, message.from_user.id, True):
            await message.answer(PHRASES_RU.replace('success.promoted_by', user_id=user_id))
        else:
            await message.answer(PHRASES_RU.error.db)


@router.command('demote', 'понизить уровень доступа', 'user_id')  # /demote
@command_arguments.user_id
async def _(message: Message, user_id):
    with UsersTable() as users_db:
        if users_db.set_admin(user_id, message.from_user.id, False):
            await message.answer(PHRASES_RU.replace('success.demoted', user_id=user_id))
        else:
            await message.answer(PHRASES_RU.error.db)


@router.command('query', 'последние N запросов', 'N')  # /query
@command_arguments.digit(default=5)
async def _(message: Message, amount: int):
    with QueriesTable() as queries_db:
        queries = queries_db.get_last_queries(int(amount))
        if not queries:
            await message.answer(PHRASES_RU.info.no_query)
            return

        txt = format_list.format_queries_text(
            queries=queries,
            footnote_template=PHRASES_RU.footnote.all_queries,
            line_template=PHRASES_RU.template.all_queries,
            show_username=True
        )

        if txt:
            await message.answer(txt.replace('\t', '\n'), disable_web_page_preview=True)


@router.command('user_query', 'запросы пользователя по ID', 'user_id')  # /user_query
@command_arguments.user_id
async def _(message: Message, user_id: int):
    await pages.user_query(message.from_user.id, user_id)


@router.command('test', 'отладка и тестирование функций')  # /test
async def _(message: Message):
    pass
