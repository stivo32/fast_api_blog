function getCookie(name) {
    return document.cookie
        .split(';')
        .map(cookie => cookie.trim())
        .find(cookie => cookie.startsWith(`${name}=`))
        ?.split('=')[1] || null;
}

async function sendRequest(url, method, body = null, jwtToken = null) {
    const headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    };

    if (jwtToken) {
        headers['Authorization'] = `Bearer ${jwtToken}`;
    }

    try {
        const response = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null,
        });

        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (jsonError) {
                console.error('Parse error JSON:', jsonError);
            }
            throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError') {
            console.error('Network error or error with CORS:', error);
        }
        console.error(`Request error: ${error.message}`);
        throw error;
    }
}
document.addEventListener('DOMContentLoaded', () => {
    const articleContainer = document.querySelector('.article-container');
    if (!articleContainer) {
        console.error('Element .article-container not found. Make sure it is present in the DOM.');
        return;
    }

    const BLOG_DATA = {
        id: articleContainer.dataset.blogId,
        status: articleContainer.dataset.blogStatus,
        author: articleContainer.dataset.blogAuthor,
        jwtToken: getCookie('users_access_token'),
    };

    console.log('BLOG_DATA:', BLOG_DATA);

    const deleteButton = document.querySelector('[data-action="delete"]');
    if (deleteButton) {
        deleteButton.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this blog?')) {
                deleteBlog(BLOG_DATA);
            }
        });
    }

    const statusButton = document.querySelector('[data-action="change-status"]');
    if (statusButton) {
        statusButton.addEventListener('click', () => {
            const newStatus = statusButton.dataset.newStatus;
            changeBlogStatus(BLOG_DATA, newStatus);
        });
    }
});

async function deleteBlog({id, jwtToken}) {
    try {
        await sendRequest(`/api/blogs/${id}`, 'DELETE', null, jwtToken);
        alert('Blog successfully deleted. Redirecting...');
        window.location.href = '/blogs/';
    } catch (error) {
        console.error('Failed to delete the blog:', error);
    }
}

async function changeBlogStatus({id, jwtToken}, newStatus) {
    try {
        const url = `/api/blogs/${id}?new_status=${encodeURIComponent(newStatus)}`;
        await sendRequest(url, 'PATCH', null, jwtToken);
        alert('Status successfully updated. The page will be refreshed.');
        location.reload();
    } catch (error) {
        console.error('Failed to change the blog status:', error);
        alert('Error updating blog status. Please try again.');
    }
}
