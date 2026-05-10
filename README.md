# Background Images for Authentication Pages

## Instructions

To add your custom background image:

1. **Place your image file** in this directory:
   - Save your image as `library-bg.jpg` in this folder
   - Recommended size: 1920x1080 or higher for best quality
   - Format: JPG, PNG, or WebP

2. **Current Setup**:
   - CSS is already configured to use `/static/images/library-bg.jpg`
   - Both login and register pages will automatically use the background
   - Image will be centered and cover the entire screen
   - Semi-transparent overlay ensures text readability

3. **Alternative Images**:
   - If you want to use a different filename, update `auth-background.css`:
   ```css
   background-image: url('/static/images/your-image-name.jpg');
   ```

4. **CSS Features**:
   - Responsive background that covers all screen sizes
   - Dark overlay for better text contrast
   - Maintains existing floating animations
   - Preserves all form functionality

## Current Files Using This Background:
- `templates/login.html`
- `templates/register.html`
- `static/css/auth-background.css`
