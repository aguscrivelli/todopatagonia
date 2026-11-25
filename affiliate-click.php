<?php

header('Cache-Control: no-store');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Allow: POST');
    http_response_code(405);
    exit;
}

if (!in_array($_SERVER['HTTP_ORIGIN'] ?? '', ['https://todopatagonia.com', 'https://www.todopatagonia.com'], true)) {
    http_response_code(403);
    exit;
}

$event = json_decode(file_get_contents('php://input', false, null, 0, 1025), true);
$page = $event['page'] ?? null;
$partner = $event['partner'] ?? null;
$placement = $event['placement'] ?? null;
if (!is_string($page) || !preg_match('~^/(?:[a-z0-9-]+/)*(?:[a-z0-9-]+\.html)?$~D', $page)
    || strlen($page) > 220 || !in_array($partner, ['booking', 'getyourguide'], true)
    || !is_string($placement) || !preg_match('/^[a-zA-Z0-9_-]{1,64}$/D', $placement)) {
    http_response_code(400);
    exit;
}

$file = __DIR__ . $page . (substr($page, -1) === '/' ? 'index.html' : '');
if (!is_file($file)) {
    http_response_code(400);
    exit;
}

$lang = substr($page, 0, 4);
$lang = in_array($lang, ['/en/', '/pt/'], true) ? substr($lang, 1, 2) : 'es';
$date = gmdate('Y-m-d');
$dir = dirname(__DIR__) . '/todo-patagonia-metrics';
if (!is_dir($dir) && !@mkdir($dir, 0700) && !is_dir($dir)) {
    http_response_code(503);
    exit;
}

$row = implode(',', [$date, $partner, $lang, $page, $placement]) . "\n";
if (@file_put_contents($dir . '/' . $date . '.csv', $row, FILE_APPEND | LOCK_EX) === false) {
    http_response_code(503);
    exit;
}
http_response_code(204);
