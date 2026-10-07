from werkzeug.wrappers import Request


class MethodOverrideMiddleware:

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        request = Request(environ)

        if request.method == "POST":

            method = request.form.get("_method", "").upper()

            if method in {
                "PUT",
                "PATCH",
                "DELETE"
            }:
                environ["REQUEST_METHOD"] = method

        return self.app(
            environ,
            start_response
        )


def init_method_override(app):

    return MethodOverrideMiddleware(app)