from datetime import datetime, timedelta
from flask import Flask, render_template_string, request
from collections import defaultdict

app = Flask(__name__)

TURNOS_DISPONIVEIS = [
    "Diurno", 
    "Noturno"
]

def gerar_escala(data_inicio_str, escala, horas_trabalho, turno_inicial_idx, tipo_fixo, mes_selecionado):
    data_atual = datetime.strptime(data_inicio_str, '%Y-%m-%d')
    
    if escala == "2x2_interrupto":
        dias_trabalho, dias_folga = 2, 2
        is_fixo = False
    elif escala == "4x2_interrupto":
        dias_trabalho, dias_folga = 4, 2
        is_fixo = False
    elif escala == "2x2_fixo":
        dias_trabalho, dias_folga = 2, 2
        is_fixo = True
    elif escala == "3x3_fixo":
        dias_trabalho, dias_folga = 3, 3
        is_fixo = True
    else:
        dias_trabalho, dias_folga = 2, 2
        is_fixo = False

    agenda_por_mes = defaultdict(list)
    turno_atual_idx = turno_inicial_idx
    
    # Geramos por um bom período (ex: 700 dias) para garantir que alcançamos o mês desejado caso a data de início seja anterior
    dias_para_gerar = 700
    dia_count = 0

    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    while dia_count < dias_para_gerar:
        # Dias de Trabalho
        for _ in range(dias_trabalho):
            data_key = data_atual.strftime('%Y-%m-%d')
            chave_mes_ano = data_atual.strftime('%Y-%m') # Ex: '2026-06'
            nome_mes = f"{meses_pt[data_atual.month]} de {data_atual.year}"
            
            if is_fixo:
                horario_texto = TURNOS_DISPONIVEIS[tipo_fixo]
            else:
                horario_texto = TURNOS_DISPONIVEIS[turno_atual_idx]
            
            agenda_por_mes[chave_mes_ano] = agenda_por_mes.get(chave_mes_ano, {"nome": nome_mes, "dias": []})
            agenda_por_mes[chave_mes_ano]["dias"].append({
                "data": data_key,
                "dia_mes": data_atual.strftime('%d/%m'),
                "tipo": "trabalho",
                "detalhes": f"Trabalho ({horas_trabalho}h)",
                "horario": horario_texto,
                "horas": horas_trabalho
            })
            data_atual += timedelta(days=1)
            dia_count += 1
        
        # Dias de Folga
        for _ in range(dias_folga):
            if dia_count >= dias_para_gerar:
                break
            data_key = data_atual.strftime('%Y-%m-%d')
            chave_mes_ano = data_atual.strftime('%Y-%m')
            nome_mes = f"{meses_pt[data_atual.month]} de {data_atual.year}"
            
            agenda_por_mes[chave_mes_ano] = agenda_por_mes.get(chave_mes_ano, {"nome": nome_mes, "dias": []})
            agenda_por_mes[chave_mes_ano]["dias"].append({
                "data": data_key,
                "dia_mes": data_atual.strftime('%d/%m'),
                "tipo": "folga",
                "detalhes": "Folga",
                "horario": "Livre",
                "horas": 0
            })
            data_atual += timedelta(days=1)
            dia_count += 1
        
        if not is_fixo:
            turno_atual_idx = (turno_atual_idx + 1) % len(TURNOS_DISPONIVEIS)

    # Filtra e retorna apenas o mês solicitado (ex: '2026-06')
    resultado_filtrado = {}
    if mes_selecionado in agenda_por_mes:
        dados_mes = agenda_por_mes[mes_selecionado]
        total_dias_trab = sum(1 for d in dados_mes["dias"] if d['tipo'] == 'trabalho')
        total_horas_trab = sum(int(d['horas']) for d in dados_mes["dias"] if d['tipo'] == 'trabalho')
        
        resultado_filtrado[dados_mes["nome"]] = {
            "dias": dados_mes["dias"],
            "total_dias": total_dias_trab,
            "total_horas": total_horas_trab
        }

    return resultado_filtrado

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agenda de Escala de Trabalho</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --trabalho-bg: rgba(59, 130, 246, 0.15);
            --trabalho-border: #3b82f6;
            --trabalho-text: #93c5fd;
            --folga-bg: rgba(16, 185, 129, 0.15);
            --folga-border: #10b981;
            --folga-text: #6ee7b7;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            color: var(--text-main);
            margin-bottom: 25px;
            font-weight: 700;
            font-size: 1.8rem;
            letter-spacing: -0.025em;
        }

        .card {
            background: var(--card-bg);
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            margin-bottom: 25px;
            border: 1px solid var(--border-color);
        }

        form {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        label {
            font-weight: 500;
            font-size: 0.875rem;
            margin-bottom: 8px;
            color: var(--text-muted);
        }

        input, select {
            padding: 12px;
            background-color: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.95rem;
            color: var(--text-main);
            outline: none;
            transition: border-color 0.2s;
        }

        input:focus, select:focus {
            border-color: var(--primary);
        }

        button.btn-submit {
            grid-column: 1 / -1;
            background-color: var(--primary);
            color: white;
            font-weight: 600;
            border: none;
            padding: 14px;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
            font-size: 1rem;
            margin-top: 10px;
        }

        button.btn-submit:hover {
            background-color: var(--primary-hover);
        }

        button.btn-submit:active {
            transform: scale(0.99);
        }

        .legenda {
            display: flex;
            gap: 25px;
            justify-content: center;
            margin-bottom: 25px;
        }

        .legenda-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--text-muted);
        }

        .box {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }

        .box-trabalho { background-color: var(--trabalho-bg); border: 2px solid var(--trabalho-border); }
        .box-folga { background-color: var(--folga-bg); border: 2px solid var(--folga-border); }

        .mes-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            margin-top: 10px;
            margin-bottom: 20px;
            padding-bottom: 12px;
        }

        h2.mes-titulo {
            color: var(--text-main);
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
        }

        .btn-imprimir {
            background-color: #059669;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            transition: background-color 0.2s;
        }

        .btn-imprimir:hover {
            background-color: #047857;
        }

        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(115px, 1fr));
            gap: 12px;
        }

        .dia-card {
            padding: 12px;
            border-radius: 10px;
            border-left: 4px solid;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 85px;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(5px);
        }

        .dia-card.trabalho {
            background-color: var(--trabalho-bg);
            border-color: var(--trabalho-border);
            color: var(--trabalho-text);
        }

        .dia-card.folga {
            background-color: var(--folga-bg);
            border-color: var(--folga-border);
            color: var(--folga-text);
        }

        .data { font-weight: 700; font-size: 0.95rem; }
        .status { font-size: 0.8rem; margin-top: 4px; font-weight: 600; }
        .horario { font-size: 0.75rem; opacity: 0.9; margin-top: 4px; }

        .relatorio-mes {
            background-color: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 15px 20px;
            margin-top: 20px;
            display: flex;
            justify-content: space-around;
            align-items: center;
            text-align: center;
        }

        .relatorio-item {
            display: flex;
            flex-direction: column;
        }

        .relatorio-valor {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-main);
        }

        .relatorio-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
        }

        @media print {
            body { background: white; color: black; }
            body * { visibility: hidden; }
            .mes-bloco.imprimindo, .mes-bloco.imprimindo * { visibility: visible; }
            .mes-bloco.imprimindo { position: absolute; left: 0; top: 0; width: 100%; }
            .btn-imprimir { display: none; }
            .dia-card { border: 1px solid #ccc !important; }
            .relatorio-mes { background: #f3f4f6 !important; border: 1px solid #d1d5db !important; color: black; }
            .relatorio-valor { color: black !important; }
            .relatorio-label { color: #4b5563 !important; }
        }
    </style>
    <script>
        function imprimirMes(elementId) {
            const bloco = document.getElementById(elementId);
            bloco.classList.add('imprimindo');
            window.print();
            bloco.classList.remove('imprimindo');
        }

        function alternarCamposTurno() {
            const escalaSelect = document.getElementById('escala');
            const grupoTurnoInterrupto = document.getElementById('grupo-turno-interrupto');
            const grupoTurnoFixo = document.getElementById('grupo-turno-fixo');

            if (escalaSelect.value.includes('fixo')) {
                grupoTurnoInterrupto.style.display = 'none';
                grupoTurnoFixo.style.display = 'flex';
            } else {
                grupoTurnoInterrupto.style.display = 'flex';
                grupoTurnoFixo.style.display = 'none';
            }
        }

        window.onload = function() {
            alternarCamposTurno();
            document.getElementById('escala').addEventListener('change', alternarCamposTurno);
        }
    </script>
</head>
<body>

<div class="container">
    <h1>🗓️ Gestão de Escalas</h1>

    <div class="card">
        <form method="POST">
            <div class="form-group">
                <label for="escala">Escala de Trabalho:</label>
                <select name="escala" id="escala" required>
                    <option value="2x2_interrupto" {% if parametros.escala == '2x2_interrupto' %}selected{% endif %}>2x2 (Interrupto)</option>
                    <option value="4x2_interrupto" {% if parametros.escala == '4x2_interrupto' %}selected{% endif %}>4x2 (Interrupto)</option>
                    <option value="2x2_fixo" {% if parametros.escala == '2x2_fixo' %}selected{% endif %}>2x2 (Fixo)</option>
                    <option value="3x3_fixo" {% if parametros.escala == '3x3_fixo' %}selected{% endif %}>3x3 (Fixo)</option>
                </select>
            </div>

            <div class="form-group">
                <label for="horas_trabalho">Carga Horária (por turno):</label>
                <input type="number" name="horas_trabalho" id="horas_trabalho" value="{{ parametros.horas_trabalho or 12 }}" required min="1" max="24">
            </div>

            <div class="form-group">
                <label for="data_inicio">Data de Início da Escala:</label>
                <input type="date" name="data_inicio" id="data_inicio" value="{{ parametros.data_inicio or '' }}" required>
            </div>

            <div class="form-group">
                <label for="mes_desejado">Mês Desejado:</label>
                <input type="month" name="mes_desejado" id="mes_desejado" value="{{ parametros.mes_desejado or '' }}" required>
            </div>

            <!-- Exibido apenas para escalas Interruptas -->
            <div class="form-group" id="grupo-turno-interrupto">
                <label for="turno_inicial">Horário do 1º Turno:</label>
                <select name="turno_inicial" id="turno_inicial">
                    <option value="0" {% if parametros.turno_inicial == 0 %}selected{% endif %}>Diurno</option>
                    <option value="1" {% if parametros.turno_inicial == 1 %}selected{% endif %}>Noturno</option>
                </select>
            </div>

            <!-- Exibido apenas para escalas Fixas -->
            <div class="form-group" id="grupo-turno-fixo" style="display: none;">
                <label for="tipo_fixo">Turno Fixo:</label>
                <select name="tipo_fixo" id="tipo_fixo">
                    <option value="0" {% if parametros.tipo_fixo == 0 %}selected{% endif %}>Diurno</option>
                    <option value="1" {% if parametros.tipo_fixo == 1 %}selected{% endif %}>Noturno</option>
                </select>
            </div>

            <button type="submit" class="btn-submit">Gerar Mês Selecionado</button>
        </form>
    </div>

    {% if agenda_por_mes %}
    <div class="card">
        <div class="legenda">
            <div class="legenda-item"><div class="box box-trabalho"></div> Dia de Trabalho</div>
            <div class="legenda-item"><div class="box box-folga"></div> Dia de Folga</div>
        </div>

        {% for mes, dados in agenda_por_mes.items() %}
            <div class="mes-bloco" id="mes-principal">
                <div class="mes-header">
                    <h2 class="mes-titulo">📅 {{ mes }}</h2>
                    <button class="btn-imprimir" onclick="imprimirMes('mes-principal')">🖨️ Imprimir Mês</button>
                </div>
                
                <div class="calendar-grid">
                    {% for info in dados.dias %}
                    <div class="dia-card {{ info.tipo }}">
                        <div class="data">{{ info.dia_mes }}</div>
                        <div class="status">{{ info.detalhes }}</div>
                        <div class="horario">{{ info.horario }}</div>
                    </div>
                    {% endfor %}
                </div>

                <div class="relatorio-mes">
                    <div class="relatorio-item">
                        <span class="relatorio-valor">{{ dados.total_dias }} dias</span>
                        <span class="relatorio-label">Dias Trabalhados</span>
                    </div>
                    <div class="relatorio-item">
                        <span class="relatorio-valor">{{ dados.total_horas }}h</span>
                        <span class="relatorio-label">Total de Horas</span>
                    </div>
                </div>
            </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="footer">
        Desenvolvido por <strong>Rafael Silva Portela</strong>
    </div>
</div>

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    agenda_por_mes = None
    parametros = {}
    
    if request.method == 'POST':
        escala = request.form.get('escala')
        horas_trabalho = int(request.form.get('horas_trabalho', 12))
        data_inicio = request.form.get('data_inicio')
        mes_desejado = request.form.get('mes_desejado') # Formato 'YYYY-MM'
        turno_inicial = int(request.form.get('turno_inicial', 0))
        tipo_fixo = int(request.form.get('tipo_fixo', 0))

        if data_inicio and mes_desejado:
            agenda_por_mes = gerar_escala(data_inicio, escala, horas_trabalho, turno_inicial, tipo_fixo, mes_desejado)
            parametros = {
                'escala': escala,
                'horas_trabalho': horas_trabalho,
                'data_inicio': data_inicio,
                'mes_desejado': mes_desejado,
                'turno_inicial': turno_inicial,
                'tipo_fixo': tipo_fixo
            }

    return render_template_string(HTML_TEMPLATE, agenda_por_mes=agenda_por_mes, parametros=parametros)

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)