document.addEventListener('DOMContentLoaded', function() {
    // Get the toggle button and nav links elements
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    // Add click event listener to the toggle button
    navToggle.addEventListener('click', function() {
        // Toggle the 'active' class on the nav links
        navLinks.classList.toggle('active');
        
        // Optionally, you can change the icon if you're using FontAwesome
        const icon = navToggle.querySelector('i');
        if (icon) {
            if (navLinks.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
    });
    
    // Close the menu when clicking outside of it
    document.addEventListener('click', function(event) {
        const isClickInsideNav = navToggle.contains(event.target) || 
                                 navLinks.contains(event.target);
        
        if (!isClickInsideNav && navLinks.classList.contains('active')) {
            navLinks.classList.remove('active');
            
            // Reset icon if using FontAwesome
            const icon = navToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
    });
    
    // Close the menu when window is resized to desktop size
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && navLinks.classList.contains('active')) {
            navLinks.classList.remove('active');
            
            // Reset icon if using FontAwesome
            const icon = navToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
    });
});