import nox


@nox.session
def check(session: nox.Session) -> None:
    session.install("poetry")
    session.run("poetry", "install")

    session.run("mypy", ".", external=True)
    session.run("ruff", ".", external=True)
    session.run("black", ".", "--check", external=True)


@nox.session
def lint(session: nox.Session) -> None:
    session.install("poetry")
    session.run("poetry", "install")

    session.run("ruff", ".", "--fix", external=True)
    session.run("black", ".", external=True)
