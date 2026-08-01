# Maintainer: Michael Cipold <github@cipold.de>
pkgname=obsidian-gnome-search-provider
pkgver=1.0.0
pkgrel=1
pkgdesc="A GNOME Shell Search Provider for Obsidian Vaults"
arch=('any')
url="https://github.com/cipold/obsidian-gnome-search-provider"
license=('MIT')
depends=('python-gobject' 'obsidian')

# For local development, we source the files directly from the repository.
# (The AUR-published version of this PKGBUILD sources the GitHub .tar.gz instead).
source=("obsidian-search-provider.py"
        "md.obsidian.Obsidian.SearchProvider.service"
        "obsidian-search-provider.ini"
        "Makefile")
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
    cd "${srcdir}"
    make DESTDIR="${pkgdir}" install
}
