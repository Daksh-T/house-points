document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light-mode';
    document.body.classList.add(currentTheme);

    // Adjust navbar based on theme
    const navbar = document.querySelector('.navbar');
    if (currentTheme === 'dark-mode') {
        navbar.classList.add('dark-mode');
    } else {
        navbar.classList.add('light-mode');
    }

    // Theme Toggle Button
    toggleButton.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        document.body.classList.toggle('light-mode');

        navbar.classList.toggle('dark-mode');
        navbar.classList.toggle('light-mode');

        let theme = 'light-mode';
        if (document.body.classList.contains('dark-mode')) {
            theme = 'dark-mode';
        }
        localStorage.setItem('theme', theme);
    });

    // Add/Subtract Button Functionality
    const addBtn = document.getElementById('add-btn');
    const subtractBtn = document.getElementById('subtract-btn');
    const actionTypeInput = document.getElementById('action_type');

    addBtn.addEventListener('click', () => {
        actionTypeInput.value = 'add';
        addBtn.classList.add('active');
        subtractBtn.classList.remove('active');
    });

    subtractBtn.addEventListener('click', () => {
        actionTypeInput.value = 'subtract';
        subtractBtn.classList.add('active');
        addBtn.classList.remove('active');
    });

    // House Selection Functionality
    const houseOptions = document.querySelectorAll('.house-option');
    houseOptions.forEach(option => {
        option.addEventListener('click', () => {
            houseOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            option.querySelector('input[type="radio"]').checked = true;
        });
    });
});
