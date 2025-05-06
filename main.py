from app import app  # noqa: F401

# If directly run (not imported)
if __name__ == "__main__":
    from app import start_app
    start_app()
