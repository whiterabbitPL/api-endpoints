(function () {

    function keepAlive() {
        fetch(WPUPS.ajax_url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                action: 'wpups_keep_alive'
            })
        })
        .then(res => {
            if (res.status === 400) {
                window.location.href = '/wp-login.php';
            }
        })
        .catch(() => {});
    }

    // co 5 minut
    setInterval(keepAlive, 5 * 60 * 1000);

})();
