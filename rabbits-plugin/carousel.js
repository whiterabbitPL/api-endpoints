document.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('.rp-carousel').forEach(carousel => {

        fetch(RP.ajax_url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                action: 'rp_get_products'
            })
        })
        .then(res => res.json())
        .then(res => {

            if (!res.success) return;

            const products = res.data;
            const track = carousel.querySelector('.rp-carousel-track');

            products.forEach(p => {
                const item = document.createElement('div');
                item.className = 'rp-item';
                item.innerHTML = `
                    <img src="${p.image}" alt="">
                    <div class="rp-info">
                        <span class="rp-price">${p.price}</span>
                        <span class="rp-stock">${p.stock}</span>
                    </div>
                `;
                track.appendChild(item);
            });

            initCarousel(carousel);
        });
    });

    function initCarousel(carousel) {
        const track = carousel.querySelector('.rp-carousel-track');
        const items = track.children;
        let index = 0;

        function update() {
            track.style.transform = `translateX(-${index * 100}%)`;
        }

        carousel.querySelector('.rp-next').onclick = () => {
            index = (index + 1) % items.length;
            update();
        };

        carousel.querySelector('.rp-prev').onclick = () => {
            index = (index - 1 + items.length) % items.length;
            update();
        };
    }

});
