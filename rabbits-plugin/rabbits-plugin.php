<?php
/**
 * Plugin Name: WP User POST Sender
 * Description: Wysyła POST z user_id na endpoint po zalogowaniu użytkownika.
 * Version: 1.0
 * Author: Your Name
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('init', function () {
    if (!session_id()) {
        session_start();
    }
});

// Hook po zalogowaniu
add_action('wp_login', 'wpups_send_user_id_on_login', 10, 2);

function wpups_send_user_id_on_login($user_login, $user) {

    // Jeśli już mamy UUID w sesji nie rejestruj ponownie
    if (!empty($_SESSION['wpups_guid'])) {
        return;
    }

    $endpoint = 'http://lab.shirousagi.pl:9000/api/register';

    $payload = array(
        'user_id' => (int) $user->ID,
    );

    $args = array(
        'body'        => wp_json_encode($payload),
        'headers'     => array(
            'Content-Type' => 'application/json',
        ),
        'timeout'     => 10,
        'data_format' => 'body',
    );

    $response = wp_remote_post($endpoint, $args);

    if (is_wp_error($response)) {
        error_log('WP User POST Sender error: ' . $response->get_error_message());
        return;
    }

    $code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);

    if ($code !== 200 || empty($body)) {
        error_log('WP User POST Sender error: Invalid response');
        return;
    }

    $data = json_decode($body, true);

    if (!isset($data['uuid'])) {
        error_log('WP User POST Sender error: UUID not found in response');
        return;
    }

    // Zapis GUID do sesji
    error_log('To tylko info');
    $_SESSION['wpups_guid'] = sanitize_text_field($data['uuid']);
}



add_action('wp_ajax_wpups_keep_alive', 'wpups_keep_alive_ajax');

function wpups_keep_alive_ajax() {

    if (!is_user_logged_in()) {
        wp_send_json_error('not_logged_in', 401);
    }

    if (empty($_SESSION['wpups_guid'])) {
        wp_send_json_error('missing_uuid', 400);
    }

    $user_id = get_current_user_id();
    $uuid    = $_SESSION['wpups_guid'];

    $endpoint = 'http://lab.shirousagi.pl:9000/api/keep-alive';

    $payload = array(
        'user_id' => $user_id,
        'uuid'    => $uuid,
    );

    $response = wp_remote_post($endpoint, array(
        'body'    => wp_json_encode($payload),
        'headers' => array('Content-Type' => 'application/json'),
        'timeout' => 10,
    ));

    if (is_wp_error($response)) {
        wp_send_json_error('api_error', 500);
    }

    $code = wp_remote_retrieve_response_code($response);

    if ($code === 400) {
        wp_logout();
        wp_send_json_error('session_expired', 400);
    }

    wp_send_json_success();
}


add_action('wp_enqueue_scripts', function () {

    if (!is_user_logged_in()) {
        return;
    }

    wp_enqueue_script(
        'wpups-keepalive',
        plugin_dir_url(__FILE__) . 'keepalive.js',
        array(),
        '1.0',
        true
    );

    wp_localize_script('wpups-keepalive', 'WPUPS', array(
        'ajax_url' => admin_url('admin-ajax.php'),
    ));
});

add_shortcode('products_carousel', function () {

    ob_start(); ?>
    <div class="rp-carousel" data-loading="1">
        <div class="rp-carousel-track"></div>
        <button class="rp-prev">‹</button>
        <button class="rp-next">›</button>
    </div>
    <?php
    return ob_get_clean();
});


add_action('wp_ajax_rp_get_products', 'rp_get_products');

function rp_get_products() {

    if (!is_user_logged_in()) {
        wp_send_json_error('not_logged_in', 401);
    }

    if (empty($_SESSION['wpups_guid'])) {
        wp_send_json_error('no_uuid', 401);
    }

    $user_id = get_current_user_id();
    $uuid    = $_SESSION['wpups_guid'];

    $endpoint = 'http://lab.shirousagi.pl:9000/api/products';

    $payload = array(
        'user_id' => $user_id,
        'uuid'    => $uuid,
    );

    $response = wp_remote_post($endpoint, array(
        'body'    => wp_json_encode($payload),
        'headers' => array('Content-Type' => 'application/json'),
        'timeout' => 10,
    ));

    if (is_wp_error($response)) {
        wp_send_json_error('api_error', 500);
    }

    $products = json_decode(wp_remote_retrieve_body($response), true);

    wp_send_json_success($products);
}

add_action('wp_enqueue_scripts', function () {

    wp_enqueue_style(
        'rp-carousel',
        plugin_dir_url(__FILE__) . 'carousel.css'
    );

    wp_enqueue_script(
        'rp-carousel',
        plugin_dir_url(__FILE__) . 'carousel.js',
        array(),
        '1.0',
        true
    );

    wp_localize_script('rp-carousel', 'RP', array(
        'ajax_url' => admin_url('admin-ajax.php')
    ));
});
