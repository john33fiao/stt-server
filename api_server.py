from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import logging

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 메모리 기반 메시지 저장소
messages = []
message_id_counter = 0
connected_clients = 0


@app.route('/')
def index():
    """웹페이지 서빙"""
    return render_template('index.html')


# WebSocket 이벤트 핸들러
@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    global connected_clients
    connected_clients += 1
    logger.info(f"Client connected. Total clients: {connected_clients}")
    emit('connection_status', {'status': 'connected', 'clients': connected_clients})


@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    global connected_clients
    connected_clients -= 1
    logger.info(f"Client disconnected. Total clients: {connected_clients}")


@socketio.on('stt_text')
def handle_stt_text(data):
    """STT 텍스트 수신 (WebSocket)"""
    global message_id_counter

    try:
        text = data.get('text')
        timestamp = data.get('timestamp')

        if not text:
            emit('stt_response', {'status': 'error', 'error': 'Text field is required'})
            return

        # 메시지 저장
        message_id_counter += 1
        message = {
            'id': message_id_counter,
            'text': text,
            'timestamp': timestamp if timestamp else datetime.now().timestamp()
        }
        messages.append(message)

        logger.info(f"Received STT text (ID: {message_id_counter}, Length: {len(text)}): {text[:50]}...")

        # 발신자에게 응답
        emit('stt_response', {'status': 'success', 'message_id': message_id_counter})

        # 모든 클라이언트에게 새 메시지 브로드캐스트
        socketio.emit('new_message', message)

    except Exception as e:
        logger.error(f"Error processing STT request: {str(e)}")
        emit('stt_response', {'status': 'error', 'error': 'Internal server error'})


@socketio.on('get_messages')
def handle_get_messages():
    """저장된 메시지 조회 (WebSocket)"""
    try:
        sorted_messages = sorted(messages, key=lambda x: x['timestamp'], reverse=True)
        emit('messages_list', {
            'status': 'success',
            'count': len(sorted_messages),
            'messages': sorted_messages
        })
    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        emit('messages_list', {'status': 'error', 'error': 'Internal server error'})


# REST API 엔드포인트 (하위 호환성 유지)
@app.route('/api/stt', methods=['POST'])
def receive_stt():
    """STT 텍스트 수신 엔드포인트 (REST - 하위 호환성)"""
    global message_id_counter

    try:
        # JSON 데이터 파싱
        data = request.get_json()

        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No data provided'}), 400

        text = data.get('text')
        timestamp = data.get('timestamp')

        if not text:
            logger.error("No text field in request")
            return jsonify({'error': 'Text field is required'}), 400

        # 메시지 저장
        message_id_counter += 1
        message = {
            'id': message_id_counter,
            'text': text,
            'timestamp': timestamp if timestamp else datetime.now().timestamp()
        }
        messages.append(message)

        logger.info(f"Received STT text via REST (ID: {message_id_counter}, Length: {len(text)}): {text[:50]}...")

        # WebSocket으로 브로드캐스트
        socketio.emit('new_message', message)

        return jsonify({
            'status': 'success',
            'message_id': message_id_counter
        }), 200

    except Exception as e:
        logger.error(f"Error processing STT request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/messages', methods=['GET'])
def get_messages():
    """저장된 메시지 조회 엔드포인트"""
    try:
        # 최근 순서로 정렬 (옵션)
        sorted_messages = sorted(messages, key=lambda x: x['timestamp'], reverse=True)

        return jsonify({
            'status': 'success',
            'count': len(sorted_messages),
            'messages': sorted_messages
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("Starting STT API Server with WebSocket on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
