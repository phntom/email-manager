from os import environ

from aiohttp import web

from em.mmapi import health, MATTERMOST_EXTERNAL

OP_URL_PREFIX = environ.get('OP_URL_PREFIX', '')


def redirect(target_url):
    return web.Response(status=302, headers={'Location': target_url}, body=f"Redirecting you to {target_url}")


def root(_):
    return redirect(MATTERMOST_EXTERNAL)


def setup_routes(bot):
    app = bot.webhook_server.app
    app.router.add_route('GET', '/_healthz', health)
    app.router.add_route('GET', '/', root)
    app.router.add_route('GET', r'/match_email/{token:[a-z0-9]+}', bot.plugins[0].match)
    return bot
