LINKEDIN_SELECTORS = {
    'login_url': 'https://www.linkedin.com/login',
    'username_field': '#username',
    'password_field': '#password',
    'login_button': '[type="submit"]',
    
    # Post selectors - updated for latest LinkedIn structure
    'post_container': '.update-components-actor,.feed-shared-update-v2,.occludable-update',
    'post_content': (
        '.feed-shared-update-v2__description-text,.feed-shared-text-view,'
        '.feed-shared-update-v2__commentary,.update-components-text'
    ),
    
    # Author selectors - updated for latest LinkedIn structure
    'post_author': (
        '.update-components-actor__name,.feed-shared-actor__name,'
        '.update-components-actor__meta,.feed-shared-actor__meta'
    ),
    'author_link': (
        '.update-components-actor__meta-link,'
        '.feed-shared-actor__meta-link,'
        '.update-components-actor__container,'
        '.feed-shared-actor__container'
    ),
    
    # Interaction selectors
    'comment_button': (
        'button[aria-label*="comment" i],'  # Case-insensitive match
        'button.comments-comment-box__submit-button,'
        '.feed-shared-comment-button'
    ),
    'comment_field': '.comments-comment-box__input'
}
