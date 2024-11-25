
document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('input[name="filter"]').forEach(radio => {
        radio.addEventListener('change', function () {
            const cards = document.querySelectorAll('.card.mb-3');
            cards.forEach(card => {
                if (this.value === 'all' ||
                    (this.value === 'correct' && card.classList.contains('border-success')) ||
                    (this.value === 'incorrect' && card.classList.contains('border-danger'))) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });


    document.querySelectorAll('.show-answer').forEach(button => {
        button.addEventListener('click', function () {
            const textElement = this.nextElementSibling;
            if (textElement.classList.contains('d-none')) {
                textElement.classList.remove('d-none');
                this.textContent = 'Hide Correct Answer';
            } else {
                textElement.classList.add('d-none');
                this.textContent = 'Show Correct Answer';
            }
        });
    });
});