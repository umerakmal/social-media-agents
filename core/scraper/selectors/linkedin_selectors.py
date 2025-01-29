LINKEDIN_SELECTORS = {
    # Login selectors
    'login_url': 'https://www.linkedin.com/login',
    'username_field': '#username',
    'password_field': '#password',
    'login_button': '[type="submit"]',
    
    # Post container selectors
    'post_container': (
        'div.feed-shared-update-v2:not([data-promoted=true]),'
        'div.relative.feed-shared-update-v2:not(.feed-shared-update-v2--sponsored)'
    ),
    
    # Post content selectors
    'post_content': (
        'div.feed-shared-update-v2__description-wrapper,'
        'div.feed-shared-text-view,'
        'div.feed-shared-update-v2__commentary,'
        'div.update-components-text,'
        'span.break-words,'
        'div.feed-shared-inline-show-more-text'
    ),
    
    # Author selectors
    'post_author': (
        'span.feed-shared-actor__name,'
        'span.update-components-actor__name,'
        'a.feed-shared-actor__container'
    ),
    'author_link': (
        'a.feed-shared-actor__container,'
        'a.update-components-actor__container,'
        'a.app-aware-link.update-components-actor__meta-link'
    ),
    
    # Reaction selectors
    'reaction_button': (
        'button.react-button,'
        'button[aria-label="React to this post"],'
        'button.artdeco-button--muted.reaction-button,'
        'button[data-control-name="react_button"],'
        'span[data-test-id="reaction-button"]'
    ),
    
    # Specific reaction selectors
    'reaction_options': {
        'LIKE': '[aria-label="Like"]',
        'CELEBRATE': '[aria-label="Celebrate"]',
        'SUPPORT': '[aria-label="Support"]',
        'FUNNY': '[aria-label="Funny"]',
        'LOVE': '[aria-label="Love"]',
        'INSIGHTFUL': '[aria-label="Insightful"]'
    },
    
    # Comment selectors
    'comment_button': (
        'button[aria-label*="comment" i],'
        'button.comments-comment-box__submit-button,'
        'button[data-control-name="comment"]'
    ),
    'comment_field': (
        'div.ql-editor[contenteditable="true"],'
        'div[role="textbox"],'
        'div.comments-comment-box__content-editor'
    ),
    'comment_submit': (
        'button[type="submit"],'
        'button.comments-comment-box__submit-button'
    )
}
