import random, asyncio
from services.fairytale_properties import enemies_by_hero_expanded, magic_items_expanded
from openai import AsyncOpenAI
from services.fairytale_properties import groups
from pathlib import Path
from aiomax.types import PhotoAttachment

HERE = Path(__file__).resolve().parent

async def load_image(bot):
    i = random.choice([1,2,3])
    pic_path = HERE / f'{i}.png'
    pic = await bot.upload_image(pic_path.read_bytes())
    return pic

async def send_fairy_picture(chat_id, bot):
    i = random.choice([1,2,3])
    pic_path = HERE / f'{i}.png'
    pic = await load_image(bot)
    await asyncio.sleep(20)
    await bot.send_message(text='', chat_id=chat_id, attachments=pic)

def get_hero_villain():
    res = random.choice(list(enemies_by_hero_expanded.items()))
    hero = res[0]
    villain = random.choice(res[1])
    return hero, villain

def get_magic_item():
    res = random.choice(list(magic_items_expanded.items()))
    item = res[0]
    use = res[1]
    return item, use

def get_query(group: int) -> str:
    query_cl = groups[group]
    hero, villain = get_hero_villain()
    item, use = get_magic_item()
    characters = f'Напиши русскую сказку. Главным героем должен быть {hero}, его соперником должен быть {villain}'
    magic_items = f'Магический предмет (не обязательный): {item} ({use})'
    age = f"Для возраста: {query_cl['min_age']} - {query_cl['max_age']}."
    length = f"Длинна: {query_cl['min_char']} - {query_cl['max_char']} слов."
    specials = f"Особенности: {query_cl['specials']}."
    query = f'{characters} {magic_items} {age} {length} {specials}'
    return query, group

SYSTEM_QUERY = 'Ты пишешь русские сказки. Используешь схему Проппа. Возвращай только сам текст сказки без упоминаний функций Проппа.'
        
async def get_story(group: int, client: AsyncOpenAI):
    # client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
    query, new_group = get_query(group)
    messages = [
            {'role': 'system', 'content': SYSTEM_QUERY},
            {"role": "user", "content": query}
        ]
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=8000,
        temperature=0.7
    ) 
    return response.choices[0].message.content, new_group

def _get_part_text(text: str, start: int, size: int) -> tuple[str, int]:
    end_signs = {'.', '!', '?', ';', ':'}
    
    # ✅ КЛЮЧЕВОЕ: если конец текста — БЕРЁМ ВСЁ
    end_pos = min(start + size, len(text))
    if end_pos >= len(text):
        return text[start:end_pos].rstrip(), end_pos - start
    
    # Обычная логика для промежуточных кусков
    chunk = text[start:end_pos]
    for i in range(len(chunk) - 1, 20, -1):
        if chunk[i] in end_signs:
            page_end = i + 1
            while page_end < len(chunk) and chunk[page_end].isspace():
                page_end += 1
            return chunk[:page_end].rstrip(), page_end
    
    return chunk.rstrip(), len(chunk)


def prepare_book(text: str, page_size: int = 3800):
    """Исправленная версия"""
    book = {}
    page_count = 1
    start = 0
    
    while start < len(text):
        page_text, actual_size = _get_part_text(text, start, page_size)
        if page_text.strip():  # пропускаем пустые
            book[page_count] = page_text.strip()
            page_count += 1
        start += actual_size
    

    return book

def ultra_clean(text: str) -> str:
    """УБИВАЕТ все проблемные символы"""
    result = []
    for char in text:
        if (char.isalnum() or      # буквы и цифры
            char in ' .,?!:;—-()[]«»""\n\t' or  # разрешённые знаки
            char.isspace()):         # пробелы
            result.append(char)
    return ''.join(result).strip()

async def send_daily_story(bot, channel_id, client):
    random_group = random.choice([1, 2, 3])
    to_sleep = 1
    tale, group = await get_story(random_group, client)
    tale_normalized = ultra_clean(tale)
    tales = prepare_book(tale_normalized)
    channel = channel_id
    
    try:
        await send_fairy_picture(channel_id, bot=bot)
        await asyncio.sleep(to_sleep)
    except Exception as e:
        print(e)
        
    for text in tales.values():
        try:
            await bot.send_message(chat_id=channel, text=text)
            await asyncio.sleep(to_sleep)
        except Exception as e:
            return False

    return True
