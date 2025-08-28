from flask import Flask, render_template, request, redirect, url_for, flash
import db
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dhnauhduoadjh12091872jdsddc'

@app.route('/')
def index():
    """Rota principal que exibe todas as informações na página inicial."""
    conn = db.get_db_connection()
    
    turmas = conn.execute('SELECT * FROM turmas ORDER BY nome').fetchall()
    alunos = conn.execute('SELECT a.id, a.nome, t.nome as turma_nome FROM alunos a JOIN turmas t ON a.turma_id = t.id ORDER BY a.nome').fetchall()
    tarefas = conn.execute('SELECT * FROM tarefas ORDER BY descricao').fetchall()
    
    resultados = conn.execute('''
        SELECT ta.descricao, al.nome as aluno_nome, tu.nome as turma_nome
        FROM tarefas ta
        JOIN alunos al ON ta.aluno_id = al.id
        JOIN turmas tu ON al.turma_id = tu.id
        WHERE ta.aluno_id IS NOT NULL
        ORDER BY tu.nome, al.nome
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', turmas=turmas, alunos=alunos, tarefas=tarefas, resultados=resultados)

@app.route('/add_turma', methods=['POST'])
def add_turma():
    nome = request.form['nome_turma'].strip()
    if nome:
        try:
            conn = db.get_db_connection()
            conn.execute('INSERT INTO turmas (nome) VALUES (?)', (nome,))
            conn.commit()
            conn.close()
            flash(f'Turma "{nome}" adicionada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao adicionar turma: {e}', 'danger')
    else:
        flash('O nome da turma não pode estar vazio.', 'warning')
    return redirect(url_for('index'))

@app.route('/add_aluno', methods=['POST'])
def add_aluno():
    nome = request.form['nome_aluno'].strip()
    turma_id = request.form['turma_id']
    if nome and turma_id:
        try:
            conn = db.get_db_connection()
            conn.execute('INSERT INTO alunos (nome, turma_id) VALUES (?, ?)', (nome, turma_id))
            conn.commit()
            conn.close()
            flash(f'Aluno "{nome}" adicionado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao adicionar aluno: {e}', 'danger')
    else:
        flash('Nome do aluno e turma são obrigatórios.', 'warning')
    return redirect(url_for('index'))

@app.route('/add_tarefa', methods=['POST'])
def add_tarefa():
    descricao = request.form['descricao_tarefa'].strip()
    if descricao:
        try:
            conn = db.get_db_connection()
            conn.execute('INSERT INTO tarefas (descricao) VALUES (?)', (descricao,))
            conn.commit()
            conn.close()
            flash(f'Tarefa "{descricao}" adicionada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao adicionar tarefa: {e}', 'danger')
    else:
        flash('A descrição da tarefa não pode estar vazia.', 'warning')
    return redirect(url_for('index'))

@app.route('/sortear', methods=['POST'])
def sortear():
    turma_id = request.form.get('turma_sorteio_id')
    if not turma_id:
        flash('Por favor, selecione uma turma para o sorteio.', 'warning')
        return redirect(url_for('index'))

    conn = db.get_db_connection()
    
    tarefa_disponivel = conn.execute('SELECT * FROM tarefas WHERE aluno_id IS NULL').fetchone()
    if not tarefa_disponivel:
        flash('Todas as tarefas já foram sorteadas!', 'info')
        conn.close()
        return redirect(url_for('index'))

    alunos_turma = conn.execute('SELECT * FROM alunos WHERE turma_id = ?', (turma_id,)).fetchall()
    if not alunos_turma:
        flash('Não há alunos cadastrados nesta turma.', 'warning')
        conn.close()
        return redirect(url_for('index'))

    contagem_tarefas = {}
    for aluno in alunos_turma:
        count = conn.execute('SELECT COUNT(id) FROM tarefas WHERE aluno_id = ?', (aluno['id'],)).fetchone()[0]
        contagem_tarefas[aluno['id']] = count
    
    min_tarefas = min(contagem_tarefas.values())
    alunos_elegiveis = [aluno_id for aluno_id, count in contagem_tarefas.items() if count == min_tarefas]
    
    aluno_sorteado_id = random.choice(alunos_elegiveis)

    conn.execute('UPDATE tarefas SET aluno_id = ? WHERE id = ?', (aluno_sorteado_id, tarefa_disponivel['id']))
    conn.commit()
    
    aluno_sorteado = conn.execute('SELECT nome FROM alunos WHERE id = ?', (aluno_sorteado_id,)).fetchone()
    turma_sorteada = conn.execute('SELECT nome FROM turmas WHERE id = ?', (turma_id,)).fetchone()
    
    flash(f'Sorteio realizado! A tarefa "{tarefa_disponivel["descricao"]}" foi atribuída a {aluno_sorteado["nome"]} da turma {turma_sorteada["nome"]}.', 'success')
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/limpar', methods=['POST'])
def limpar():
    try:
        conn = db.get_db_connection()
        conn.execute('UPDATE tarefas SET aluno_id = NULL')
        conn.commit()
        conn.close()
        flash('Todos os sorteios foram limpos! As tarefas estão disponíveis novamente.', 'info')
    except Exception as e:
        flash(f'Ocorreu um erro ao limpar os sorteios: {e}', 'danger')
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True)
