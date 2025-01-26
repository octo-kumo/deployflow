from deployflow.core.analysis.fs import init_target


def common_tests(target, subdir=""):
    ls, cat, close = init_target(target)
    try:
        assert set(ls(subdir)) == {subdir + "app/", subdir + "README.md", subdir + '.gitignore'}
        assert "Simple Deploy App with Frontend and Backend" in cat(subdir + "README.md")
        assert set(ls(subdir + "app/")) == {subdir + "app/app.py", subdir + "app/templates/",
                                            subdir + "app/requirements.txt",
                                            subdir + "app/static/"}
        assert "from flask import Flask" in cat(subdir + "app/app.py")
        assert set(ls(subdir + "app/templates/")) == {subdir + "app/templates/index.html"}
        assert "<title>Simple Deploy App</title>" in cat(subdir + "app/templates/index.html")
    finally:
        close()


def test_git_repo_remote():
    repo_url = "https://github.com/Arvo-AI/hello_world.git"
    common_tests(repo_url)


def test_local():
    repo_url = "C:\\Users\\zy\\Downloads\\hello_world-main"
    common_tests(repo_url)


def test_local_zip():
    repo_url = "C:\\Users\\zy\\Downloads\\hello_world-main.zip"
    common_tests(repo_url, "hello_world-main/")


def test_local_tar():
    repo_url = "C:\\Users\\zy\\Downloads\\hello_world-main.tar"
    common_tests(repo_url, "hello_world-main/")


def test_nested_zip():
    repo_url = "C:\\Users\\zy\\Downloads\\nested2.zip"
    common_tests(repo_url, 'nested2/nested/hello_world-main/')
