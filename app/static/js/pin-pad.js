class PinPad {
    constructor(padId, dotsId, deleteId, maxLength) {
        this.value = '';
        this.maxLength = maxLength || 6;
        this.dotsEl = document.getElementById(dotsId);
        this.padEl = document.getElementById(padId);
        this.deleteEl = document.getElementById(deleteId);

        this.padEl.querySelectorAll('[data-digit]').forEach(btn => {
            btn.addEventListener('click', () => {
                if (this.value.length < this.maxLength) {
                    this.value += btn.dataset.digit;
                    this.render();
                }
            });
        });

        this.deleteEl.addEventListener('click', () => {
            this.value = this.value.slice(0, -1);
            this.render();
        });
    }

    render() {
        this.dotsEl.textContent = '\u2022'.repeat(this.value.length);
    }

    getValue() {
        return this.value;
    }

    clear() {
        this.value = '';
        this.render();
    }
}
