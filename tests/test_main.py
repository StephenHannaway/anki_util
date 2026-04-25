from anki_sync.main import main


def test_main(capsys):
    main()
    captured = capsys.readouterr()
    assert "Hello from anki-sync" in captured.out
