document.addEventListener('DOMContentLoaded', function() {
    // Project configurations
    const projects = {
        tgfs: {
            name: 'MCS-TGFS',
            icon: 'fa-piggy-bank',
            redirect: 'dashboard.html'
        },
        finance: {
            name: 'Mushana Finance Services',
            icon: 'fa-hand-holding-usd',
            redirect: '#'
        },
        realestate: {
            name: 'Real Estate Projects',
            icon: 'fa-home',
            redirect: '#'
        },
        sacco: {
            name: 'SACCO Share Holder',
            icon: 'fa-users',
            redirect: '#'
        }
    };

    // Handle login button clicks
    document.querySelectorAll('.login-btn').forEach(button => {
        button.addEventListener('click', function() {
            const projectCard = this.closest('.project-card');
            const projectType = projectCard.dataset.project;
            const project = projects[projectType];

            // Update modal content
            document.getElementById('loginModalTitle').textContent = 
                `Login to ${project.name}`;
            document.getElementById('modalProjectIcon').innerHTML = 
                `<i class="fas ${project.icon}"></i>`;

            // Store selected project for form submission
            document.getElementById('loginForm').dataset.project = projectType;

            loginModal.show();
        });
    });

    // Handle password visibility toggle
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    togglePassword.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        this.querySelector('i').classList.toggle('fa-eye');
        this.querySelector('i').classList.toggle('fa-eye-slash');
    });

    // Handle form submission
    document.getElementById('loginForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const projectType = this.dataset.project;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // Here you would typically make an API call to verify credentials
        console.log(`Logging in to ${projectType} with username: ${username}`);

        // For demonstration, we'll redirect to the TGFS dashboard
        if (projectType === 'tgfs') {
            window.location.href = projects[projectType].redirect;
        } else {
            alert('Project access coming soon!');
        }
    });

    // Clear form when modal is hidden
    document.getElementById('loginModal').addEventListener('hidden.bs.modal', function () {
        document.getElementById('loginForm').reset();
        togglePassword.querySelector('i').className = 'fas fa-eye';
        passwordInput.type = 'password';
    });
});