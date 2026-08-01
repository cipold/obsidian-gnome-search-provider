PREFIX ?= /usr
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share

all:
	@echo "Run 'make install' to install."
	@echo "Run 'make lint' to check code quality."
	@echo "Run 'make format' to auto-format code."

install:
	install -Dm755 obsidian-search-provider.py $(DESTDIR)$(BINDIR)/obsidian-search-provider
	install -Dm644 md.obsidian.Obsidian.SearchProvider.service $(DESTDIR)$(DATADIR)/dbus-1/services/md.obsidian.Obsidian.SearchProvider.service
	install -Dm644 obsidian-search-provider.ini $(DESTDIR)$(DATADIR)/gnome-shell/search-providers/obsidian-search-provider.ini

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/obsidian-search-provider
	rm -f $(DESTDIR)$(DATADIR)/dbus-1/services/md.obsidian.Obsidian.SearchProvider.service
	rm -f $(DESTDIR)$(DATADIR)/gnome-shell/search-providers/obsidian-search-provider.ini

lint:
	uv run ruff check obsidian-search-provider.py
	uv run mypy obsidian-search-provider.py

format:
	uv run ruff check --fix obsidian-search-provider.py
	uv run ruff format obsidian-search-provider.py
