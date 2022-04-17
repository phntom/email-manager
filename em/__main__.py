import asyncio

if __name__ == '__main__':
    from em.bot import tasks

    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
