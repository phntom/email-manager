import asyncio

if __name__ == '__main__':
    from em.bot import get_bot
    tasks = [asyncio.get_event_loop().create_task(get_bot().run())]
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
