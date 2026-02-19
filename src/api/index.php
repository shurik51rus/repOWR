<?php
// CORS заголовки для работы со сторонних сайтов
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Max-Age: 86400');

// Обработка preflight запроса браузера
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Путь к базе данных SQLite
$db_path = __DIR__ . '/../repowr_data/reputation.db';

// Параметры из URL
$endpoint = $_GET['endpoint'] ?? 'health';
$address  = $_GET['address'] ?? '';
$limit    = max(1, min(50, intval($_GET['limit'] ?? 5))); // от 1 до 50

// ===== HEALTH =====
if ($endpoint === 'health') {
    echo json_encode([
        'success'  => true,
        'message'  => 'API is running',
        'version'  => '2.0.0',
        'protocol' => 'repOWR'
    ], JSON_PRETTY_PRINT);
    exit;
}

// Открываем базу данных (только чтение)
try {
    $db = new PDO('sqlite:' . $db_path, null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Database unavailable']);
    exit;
}

// ===== Вспомогательная функция: получить профиль по адресу =====
function getProfile($db, $address) {
    // Берём последний профиль для этого адреса
    $stmt = $db->prepare("
        SELECT nickname, bio, avatar, skills, location, links
        FROM profiles
        WHERE address = ?
        ORDER BY id DESC
        LIMIT 1
    ");
    $stmt->execute([$address]);
    return $stmt->fetch(PDO::FETCH_ASSOC) ?: null;
}

// ===== Вспомогательная функция: рассчитать репутацию адреса =====
function getReputation($db, $address) {
    // Считаем оценки где адрес является получателем транзакции
    $stmt = $db->prepare("
        SELECT
            COUNT(r.id)        AS total_ratings,
            AVG(r.rating)      AS avg_rating,
            MIN(r.rating)      AS min_rating,
            MAX(r.rating)      AS max_rating
        FROM ratings r
        JOIN transactions t ON r.tx_id = t.id
        WHERE t.receiver = ? AND t.is_valid = 1
    ");
    $stmt->execute([$address]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);

    // Считаем сколько оценок дал сам адрес
    $stmt2 = $db->prepare("
        SELECT COUNT(r.id) AS ratings_given
        FROM ratings r
        JOIN transactions t ON r.tx_id = t.id
        WHERE t.sender = ? AND t.is_valid = 1
    ");
    $stmt2->execute([$address]);
    $given = $stmt2->fetch(PDO::FETCH_ASSOC);

    $avg   = $row['avg_rating'] ? round((float)$row['avg_rating'], 2) : 0;
    $total = (int)$row['total_ratings'];

    // Итоговый балл: среднее × логарифм количества (чем больше отзывов, тем выше вес)
    $final = $total > 0 ? round($avg * log($total + 1), 2) : 0;

    return [
        'final_score'   => $final,
        'avg_rating'    => $avg,
        'total_ratings' => $total,
        'ratings_given' => (int)$given['ratings_given'],
        'min_rating'    => $row['min_rating'] ? (int)$row['min_rating'] : null,
        'max_rating'    => $row['max_rating'] ? (int)$row['max_rating'] : null,
    ];
}

try {
    switch ($endpoint) {

        // ===== REPUTATION: репутация одного адреса =====
        case 'reputation':
            if (empty($address)) {
                echo json_encode(['success' => false, 'error' => 'Address required']);
                exit;
            }

            $rep     = getReputation($db, $address);
            $profile = getProfile($db, $address);

            $data = ['address' => $address, 'reputation' => $rep];
            if ($profile) $data['profile'] = $profile;

            echo json_encode(['success' => true, 'data' => $data], JSON_UNESCAPED_UNICODE);
            break;

        // ===== REVIEWS: отзывы для адреса =====
        case 'reviews':
            if (empty($address)) {
                echo json_encode(['success' => false, 'error' => 'Address required']);
                exit;
            }

            // Полученные отзывы
            $stmt = $db->prepare("
                SELECT r.rating, r.type, r.comment, r.link, t.sender, t.timestamp
                FROM ratings r
                JOIN transactions t ON r.tx_id = t.id
                WHERE t.receiver = ? AND t.is_valid = 1
                ORDER BY t.timestamp DESC
                LIMIT ?
            ");
            $stmt->execute([$address, $limit]);
            $received = $stmt->fetchAll(PDO::FETCH_ASSOC);

            // Добавляем никнейм отправителя
            foreach ($received as &$r) {
                $p = getProfile($db, $r['sender']);
                $r['sender_name']   = $p ? $p['nickname'] : null;
                $r['sender_avatar'] = $p ? $p['avatar']   : null;
            }

            // Выданные отзывы
            $stmt2 = $db->prepare("
                SELECT r.rating, r.type, r.comment, r.link, t.receiver, t.timestamp
                FROM ratings r
                JOIN transactions t ON r.tx_id = t.id
                WHERE t.sender = ? AND t.is_valid = 1
                ORDER BY t.timestamp DESC
                LIMIT ?
            ");
            $stmt2->execute([$address, $limit]);
            $given = $stmt2->fetchAll(PDO::FETCH_ASSOC);

            // Добавляем никнейм получателя
            foreach ($given as &$r) {
                $p = getProfile($db, $r['receiver']);
                $r['receiver_name']   = $p ? $p['nickname'] : null;
                $r['receiver_avatar'] = $p ? $p['avatar']   : null;
            }

            echo json_encode([
                'success' => true,
                'data'    => ['address' => $address, 'received' => $received, 'given' => $given]
            ], JSON_UNESCAPED_UNICODE);
            break;

        // ===== TOP: топ пользователей =====
        case 'top':
            // Получаем всех получателей валидных оценок
            $stmt = $db->prepare("
                SELECT t.receiver AS address,
                       COUNT(r.id)   AS total_ratings,
                       AVG(r.rating) AS avg_rating
                FROM ratings r
                JOIN transactions t ON r.tx_id = t.id
                WHERE t.is_valid = 1
                GROUP BY t.receiver
                HAVING total_ratings >= 1
                ORDER BY avg_rating DESC, total_ratings DESC
                LIMIT ?
            ");
            $stmt->execute([$limit]);
            $users = $stmt->fetchAll(PDO::FETCH_ASSOC);

            $result = [];
            foreach ($users as $user) {
                $avg   = round((float)$user['avg_rating'], 2);
                $total = (int)$user['total_ratings'];
                $final = round($avg * log($total + 1), 2);

                $data = [
                    'address'    => $user['address'],
                    'reputation' => [
                        'final_score'   => $final,
                        'avg_rating'    => $avg,
                        'total_ratings' => $total,
                    ]
                ];

                $p = getProfile($db, $user['address']);
                if ($p) $data['profile'] = $p;

                $result[] = $data;
            }

            // Сортируем по итоговому баллу
            usort($result, fn($a, $b) => $b['reputation']['final_score'] <=> $a['reputation']['final_score']);

            echo json_encode(['success' => true, 'data' => $result], JSON_UNESCAPED_UNICODE);
            break;

        // ===== STATS: общая статистика =====
        case 'stats':
            $stats = $db->query("
                SELECT
                    (SELECT COUNT(DISTINCT t.receiver) FROM transactions t
                     JOIN ratings r ON r.tx_id = t.id WHERE t.is_valid = 1) AS total_users,
                    (SELECT COUNT(*) FROM ratings r
                     JOIN transactions t ON r.tx_id = t.id WHERE t.is_valid = 1) AS total_ratings,
                    (SELECT COUNT(DISTINCT address) FROM profiles)             AS total_profiles,
                    (SELECT AVG(r.rating) FROM ratings r
                     JOIN transactions t ON r.tx_id = t.id WHERE t.is_valid = 1) AS avg_rating
            ")->fetch(PDO::FETCH_ASSOC);

            echo json_encode([
                'success' => true,
                'data'    => [
                    'total_users'    => (int)$stats['total_users'],
                    'total_ratings'  => (int)$stats['total_ratings'],
                    'total_profiles' => (int)$stats['total_profiles'],
                    'avg_rating'     => $stats['avg_rating'] ? round((float)$stats['avg_rating'], 2) : 0,
                ]
            ], JSON_PRETTY_PRINT);
            break;

        default:
            echo json_encode([
                'error'     => 'Unknown endpoint',
                'available' => ['health', 'reputation', 'reviews', 'top', 'stats']
            ]);
    }

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>