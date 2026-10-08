import subprocess
import sys

# Verificação e instalação automática das dependências necessárias
def verificar_e_instalar():
    for pacote, modulo in [('flask', 'flask'), ('pillow', 'PIL')]:
        try:
            __import__(modulo)
        except ImportError:
            print(f"Biblioteca '{pacote}' não encontrada. Instalando automaticamente...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])

verificar_e_instalar()

import os
import io
import base64
import json
import webbrowser
from threading import Timer
from flask import Flask, render_template_string, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont, ImageOps

app = Flask(__name__)
PASTA_SAIDA = os.path.join(os.getcwd(), 'saida_pranchas')
os.makedirs(PASTA_SAIDA, exist_ok=True)

ARQUIVOS_MEMORIA = []
Nomes_Arquivos_Memoria = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Lorica - Gerador de Figuras</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; margin: 0; padding: 10px; color: #e0e0e0; }
        .main-layout { display: flex; gap: 15px; width: 100%; max-width: 100%; box-sizing: border-box; align-items: flex-start; }
        .panel-form { flex: 0 0 460px; background: #1e1e1e; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        .panel-preview { flex: 1; background: #1e1e1e; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); position: sticky; top: 10px; text-align: center; }
        
        .app-header { display: flex; align-items: center; gap: 12px; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 12px; }
        .app-logo { width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #3a86ff; }
        .app-titles h2 { color: #3a86ff; margin: 0 0 2px 0; font-size: 22px; }
        .sub-header { font-size: 11px; color: #888; margin: 0; }
        
        .tabs { display: flex; cursor: pointer; background: #2c2c2c; border-radius: 4px 4px 0 0; overflow: hidden; margin-bottom: 15px; flex-wrap: wrap; }
        .tab { flex: 1; min-width: 90px; padding: 8px 4px; text-align: center; font-weight: bold; background: #2c2c2c; color: #bbb; border: none; transition: 0.3s; font-size: 10px; }
        .tab.active { background: #3a86ff; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .form-group { margin-bottom: 12px; }
        label { display: block; margin-bottom: 4px; font-weight: bold; font-size: 12px; color: #ccc; }
        input[type="file"], input[type="text"], input[type="number"], select { width: 100%; padding: 7px; box-sizing: border-box; border: 1px solid #444; background: #2a2a2a; color: #fff; border-radius: 4px; font-size: 13px; }
        
        .ordem-lista { background: #252525; border: 1px solid #444; border-radius: 4px; max-height: 150px; overflow-y: auto; padding: 5px; margin-top: 5px; }
        .ordem-item { display: flex; align-items: center; justify-content: space-between; background: #2e2e2e; padding: 4px 8px; margin-bottom: 4px; border-radius: 3px; font-size: 11px; }
        .ordem-item span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 240px; }
        .btn-ordem { background: #444; color: #fff; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 10px; margin-left: 2px; }
        .btn-ordem:hover { background: #3a86ff; }

        .color-picker-wrapper { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; margin-top: 4px; }
        .color-btn { width: 26px; height: 26px; border-radius: 50%; border: 2px solid #555; cursor: pointer; padding: 0; outline: none; transition: transform 0.1s; }
        .color-btn:hover { transform: scale(1.1); border-color: #fff; }
        .custom-color-input { width: 32px; height: 28px; border: none; background: none; cursor: pointer; padding: 0; }
        
        .export-box { margin-top: 15px; background: #252525; padding: 12px; border-radius: 6px; border: 1px solid #333; text-align: left; }
        .export-box label { font-size: 11px; margin-bottom: 3px; }
        .export-box select { margin-bottom: 8px; }
        .btn-success { background: #38b000; text-decoration: none; display: inline-block; text-align: center; color: white; padding: 10px; border-radius: 4px; width: 100%; box-sizing: border-box; font-weight: bold; font-size: 14px; border: none; cursor: pointer; }
        .btn-success:hover { background: #2b8a00; }
        
        .preview-img { max-width: 100%; max-height: 75vh; height: auto; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.5); border: 1px solid #333; }
        .info-status { background: #132a13; padding: 6px; border-radius: 4px; margin-bottom: 8px; font-size: 12px; color: #52b788; border: 1px solid #2d6a4f; }
        .aviso-vazio { color: #777; font-style: italic; padding: 40px 0; }
        .sub-config { background: #252525; padding: 10px; border-radius: 4px; margin-top: 8px; border: 1px solid #333; }
    </style>
    <script>
        function mudarAba(evt, idAba) {
            var contents = document.getElementsByClassName("tab-content");
            for (var i = 0; i < contents.length; i++) { contents[i].classList.remove("active"); }
            var tabs = document.getElementsByClassName("tab");
            for (var i = 0; i < tabs.length; i++) { tabs[i].classList.remove("active"); }
            document.getElementById(idAba).classList.add("active");
            evt.currentTarget.classList.add("active");
        }
        
        function toggleModoTamanho() {
            var modo = document.getElementById("modo_tamanho_foto").value;
            document.getElementById("configs_tamanho_personalizado").style.display = (modo === "personalizado") ? "block" : "none";
        }

        function toggleQuadroConfig() {
            var usarQuadro = document.getElementById("usar_quadro").value;
            document.getElementById("configs_quadro").style.display = (usarQuadro === "sim") ? "block" : "none";
        }

        function toggleCaixaConfig() {
            var usarCaixa = document.getElementById("usar_caixa_legenda").value;
            document.getElementById("configs_caixa").style.display = (usarCaixa === "sim") ? "block" : "none";
        }

        function definirCor(hiddenId, corHex) {
            document.getElementById(hiddenId).value = corHex;
            atualizarPreview();
        }

        function moverItem(index, direcao) {
            var inputOrdem = document.getElementById("ordem_indices");
            var ordem = JSON.parse(inputOrdem.value);
            
            var novoIndex = index + direcao;
            if (novoIndex >= 0 && novoIndex < ordem.length) {
                var temp = ordem[index];
                ordem[index] = ordem[novoIndex];
                ordem[novoIndex] = temp;
                inputOrdem.value = JSON.stringify(ordem);
                atualizarPreview();
            }
        }

        function atualizarPreview() {
            var form = document.getElementById("form-prancha");
            var formData = new FormData(form);

            fetch('/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(html => {
                var parser = new DOMParser();
                var doc = parser.parseFromString(html, 'text/html');
                document.getElementById('container-preview').innerHTML = doc.getElementById('container-preview').innerHTML;
                
                var novaLista = doc.getElementById('container-ordem-lista');
                if(novaLista) {
                    document.getElementById('container-ordem-lista').innerHTML = novaLista.innerHTML;
                }
            })
            .catch(error => console.error('Erro ao atualizar preview:', error));
        }

        window.onload = function() {
            toggleModoTamanho();
            toggleQuadroConfig();
            toggleCaixaConfig();
            
            var campos = document.querySelectorAll('input, select');
            campos.forEach(function(campo) {
                if(campo.type !== 'color' && campo.id !== 'resolucao_dpi' && campo.id !== 'ordem_indices' && campo.type !== 'file') {
                    campo.addEventListener('change', atualizarPreview);
                    if(campo.type === 'number' || campo.type === 'text') {
                        campo.addEventListener('input', atualizarPreview);
                    }
                }
            });

            var inputFiles = document.querySelector('input[type="file"]');
            if(inputFiles) {
                inputFiles.addEventListener('change', function() {
                    document.getElementById("form-prancha").submit();
                });
            }
        }
    </script>
</head>
<body>
    <div class="main-layout">
        <div class="panel-form">
            <div class="app-header">
                <img src="/logo.png" alt="Logo Lorica" class="app-logo">
                <div class="app-titles">
                    <h2>Lorica</h2>
                    <div class="sub-header">Versão 1.0 &bull; Criado por: Gilberto Salvador</div>
                </div>
            </div>
            
            <div class="tabs">
                <button type="button" class="tab active" onclick="mudarAba(event, 'aba1')">1. Grade & Imagens</button>
                <button type="button" class="tab" onclick="mudarAba(event, 'aba2')">2. Fundo & Espaço</button>
                <button type="button" class="tab" onclick="mudarAba(event, 'aba3')">3. Identificação</button>
                <button type="button" class="tab" onclick="mudarAba(event, 'aba4')">4. Título</button>
            </div>

            <form id="form-prancha" method="POST" enctype="multipart/form-data">
                <input type="hidden" name="ordem_indices" id="ordem_indices" value='{{ ordem_indices_json | safe }}'>

                <!-- ABA 1: Grade, Imagens e Formato -->
                <div id="aba1" class="tab-content active">
                    {% if total_imagens > 0 %}
                    <div class="info-status">✔ {{ total_imagens }} imagem(ns) carregada(s).</div>
                    {% endif %}
                    
                    <div class="form-group">
                        <label>Selecionar Novas Imagens:</label>
                        <input type="file" name="imagens" multiple accept="image/*">
                    </div>
                    <div class="form-group">
                        <label>Número de Colunas:</label>
                        <input type="number" name="cols" value="{{ cols }}" min="1" required>
                    </div>
                    <div class="form-group">
                        <label>Número de Linhas:</label>
                        <input type="number" name="rows" value="{{ rows }}" min="1" required>
                    </div>

                    <div class="form-group">
                        <label>Ordem Manual das Figuras:</label>
                        <div id="container-ordem-lista" class="ordem-lista">
                            {% if nomes_arquivos %}
                                {% for idx in ordem_indices %}
                                <div class="ordem-item">
                                    <span>{{ loop.index }}. {{ nomes_arquivos[idx] }}</span>
                                    <div>
                                        <button type="button" class="btn-ordem" onclick="moverItem({{ loop.index0 }}, -1)">▲</button>
                                        <button type="button" class="btn-ordem" onclick="moverItem({{ loop.index0 }}, 1)">▼</button>
                                    </div>
                                </div>
                                {% endfor %}
                            {% else %}
                                <div style="text-align: center; color: #777; font-size: 11px; padding: 10px;">Nenhuma imagem carregada</div>
                            {% endif %}
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Formato / Tamanho das Imagens:</label>
                        <select name="modo_tamanho_foto" id="modo_tamanho_foto" onchange="toggleModoTamanho()">
                            <option value="original" {% if modo_tamanho_foto == 'original' %}selected{% endif %}>Manter o tamanho original (Proporcional)</option>
                            <option value="personalizado" {% if modo_tamanho_foto == 'personalizado' %}selected{% endif %}>Definir tamanho do quadro</option>
                        </select>
                    </div>
                    <div id="configs_tamanho_personalizado" class="sub-config">
                        <div class="form-group">
                            <label>Largura do Quadro (cm):</label>
                            <input type="number" step="0.1" name="largura_quadro_cm" value="{{ largura_quadro_cm }}" min="1" max="100">
                        </div>
                        <div class="form-group">
                            <label>Altura do Quadro (cm):</label>
                            <input type="number" step="0.1" name="altura_quadro_cm" value="{{ altura_quadro_cm }}" min="1" max="100">
                        </div>
                        <div class="form-group">
                            <label>Ajustar por / Comportamento:</label>
                            <select name="ajuste_por">
                                <option value="conter_sem_cortes" {% if ajuste_por == 'conter_sem_cortes' %}selected{% endif %}>Conter (Sem cortar nenhuma parte)</option>
                                <option value="preencher_com_cortes" {% if ajuste_por == 'preencher_com_cortes' %}selected{% endif %}>Preencher / Cobrir (Pode cortar ao centro)</option>
                                <option value="largura" {% if ajuste_por == 'largura' %}selected{% endif %}>Ajustar pela Largura exata</option>
                                <option value="altura" {% if ajuste_por == 'altura' %}selected{% endif %}>Ajustar pela Altura exata</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- ABA 2: Espaço, Fundo e Quadro -->
                <div id="aba2" class="tab-content">
                    <div class="form-group">
                        <label>Cor do Fundo da Prancha:</label>
                        <input type="hidden" name="cor_fundo" id="cor_fundo_val" value="{{ cor_fundo }}">
                        <div class="color-picker-wrapper">
                            <button type="button" class="color-btn" style="background:#000000;" onclick="definirCor('cor_fundo_val', '#000000')"></button>
                            <button type="button" class="color-btn" style="background:#ffffff;" onclick="definirCor('cor_fundo_val', '#ffffff')"></button>
                            <input type="color" class="custom-color-input" value="{{ cor_fundo }}" onchange="definirCor('cor_fundo_val', this.value)">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Distância (Espaçamento em pixels):</label>
                        <input type="number" name="gap" value="{{ gap }}" min="0" max="100">
                    </div>
                    <div class="form-group">
                        <label>Deseja inserir Quadro ao redor das fotos?</label>
                        <select name="usar_quadro" id="usar_quadro" onchange="toggleQuadroConfig()">
                            <option value="sim" {% if usar_quadro == 'sim' %}selected{% endif %}>Sim, com quadro</option>
                            <option value="nao" {% if usar_quadro == 'nao' %}selected{% endif %}>Não</option>
                        </select>
                    </div>
                    <div id="configs_quadro" class="sub-config">
                        <div class="form-group">
                            <label>Espessura do Quadro/Borda (pixels):</label>
                            <input type="number" name="borda_foto" value="{{ borda_foto }}" min="1" max="20">
                        </div>
                        <div class="form-group">
                            <label>Cor do Quadro/Borda da Foto:</label>
                            <input type="hidden" name="cor_quadro" id="cor_quadro_val" value="{{ cor_quadro }}">
                            <div class="color-picker-wrapper">
                                <button type="button" class="color-btn" style="background:#000000;" onclick="definirCor('cor_quadro_val', '#000000')"></button>
                                <button type="button" class="color-btn" style="background:#ffffff;" onclick="definirCor('cor_quadro_val', '#ffffff')"></button>
                                <input type="color" class="custom-color-input" value="{{ cor_quadro }}" onchange="definirCor('cor_quadro_val', this.value)">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ABA 3: Identificação -->
                <div id="aba3" class="tab-content">
                    <div class="form-group">
                        <label>Estilo de Legenda (Identificação):</label>
                        <select name="estilo">
                            <option value="0" {% if estilo == '0' %}selected{% endif %}>Sem legendas</option>
                            <option value="1" {% if estilo == '1' %}selected{% endif %}>Maiúsculas (A, B, C...)</option>
                            <option value="2" {% if estilo == '2' %}selected{% endif %}>Minúsculas (a, b, c...)</option>
                            <option value="3" {% if estilo == '3' %}selected{% endif %}>Romanos (i, ii, iii...)</option>
                            <option value="4" {% if estilo == '4' %}selected{% endif %}>Números (1, 2, 3...)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Posição da Identificação na Foto:</label>
                        <select name="posicao">
                            <option value="sup_esq" {% if posicao == 'sup_esq' %}selected{% endif %}>Superior Esquerdo</option>
                            <option value="sup_dir" {% if posicao == 'sup_dir' %}selected{% endif %}>Superior Direito</option>
                            <option value="inf_esq" {% if posicao == 'inf_esq' %}selected{% endif %}>Inferior Esquerdo</option>
                            <option value="inf_dir" {% if posicao == 'inf_dir' %}selected{% endif %}>Inferior Direito</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Família da Fonte:</label>
                        <select name="fonte_familia">
                            <option value="arial" {% if fonte_familia == 'arial' %}selected{% endif %}>Arial</option>
                            <option value="times" {% if fonte_familia == 'times' %}selected{% endif %}>Times New Roman</option>
                            <option value="cour" {% if fonte_familia == 'cour' %}selected{% endif %}>Courier New</option>
                            <option value="calibri" {% if fonte_familia == 'calibri' %}selected{% endif %}>Calibri</option>
                            <option value="aptos" {% if fonte_familia == 'aptos' %}selected{% endif %}>Aptos</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Estilo da Fonte:</label>
                        <select name="fonte_estilo">
                            <option value="normal" {% if fonte_estilo == 'normal' %}selected{% endif %}>Normal</option>
                            <option value="bold" {% if fonte_estilo == 'bold' %}selected{% endif %}>Negrito</option>
                            <option value="italic" {% if fonte_estilo == 'italic' %}selected{% endif %}>Itálico</option>
                            <option value="bolditalic" {% if fonte_estilo == 'bolditalic' %}selected{% endif %}>Negrito e Itálico</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Tamanho da Fonte da Identificação (px):</label>
                        <input type="number" name="tamanho_fonte_legenda" value="{{ tamanho_fonte_legenda }}" min="12" max="96">
                    </div>
                    <div class="form-group">
                        <label>Cor do Texto da Identificação:</label>
                        <input type="hidden" name="cor_texto" id="cor_texto_val" value="{{ cor_texto }}">
                        <div class="color-picker-wrapper">
                            <button type="button" class="color-btn" style="background:#000000;" onclick="definirCor('cor_texto_val', '#000000')"></button>
                            <button type="button" class="color-btn" style="background:#ffffff;" onclick="definirCor('cor_texto_val', '#ffffff')"></button>
                            <input type="color" class="custom-color-input" value="{{ cor_texto }}" onchange="definirCor('cor_texto_val', this.value)">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Deseja caixa de fundo ao redor do texto?</label>
                        <select name="usar_caixa_legenda" id="usar_caixa_legenda" onchange="toggleCaixaConfig()">
                            <option value="sim" {% if usar_caixa_legenda == 'sim' %}selected{% endif %}>Sim</option>
                            <option value="nao" {% if usar_caixa_legenda == 'nao' %}selected{% endif %}>Não</option>
                        </select>
                    </div>
                    <div id="configs_caixa" class="sub-config">
                        <div class="form-group">
                            <label>Formato da Caixa/Identificador:</label>
                            <select name="formato_caixa">
                                <option value="circulo" {% if formato_caixa == 'circulo' %}selected{% endif %}>Círculo / Oval</option>
                                <option value="retangulo" {% if formato_caixa == 'retangulo' %}selected{% endif %}>Retângulo / Quadrado</option>
                                <option value="arredondado" {% if formato_caixa == 'arredondado' %}selected{% endif %}>Cantos Arredondados</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Cor de Fundo da Caixa:</label>
                            <input type="hidden" name="cor_fundo_caixa" id="cor_fundo_caixa_val" value="{{ cor_fundo_caixa }}">
                            <div class="color-picker-wrapper">
                                <button type="button" class="color-btn" style="background:#000000;" onclick="definirCor('cor_fundo_caixa_val', '#000000')"></button>
                                <button type="button" class="color-btn" style="background:#ffffff;" onclick="definirCor('cor_fundo_caixa_val', '#ffffff')"></button>
                                <input type="color" class="custom-color-input" value="{{ cor_fundo_caixa }}" onchange="definirCor('cor_fundo_caixa_val', this.value)">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Deseja borda ao redor da caixa de texto?</label>
                            <select name="usar_borda_caixa">
                                <option value="sim" {% if usar_borda_caixa == 'sim' %}selected{% endif %}>Sim</option>
                                <option value="nao" {% if usar_borda_caixa == 'nao' %}selected{% endif %}>Não</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Cor da Borda da Caixa:</label>
                            <input type="hidden" name="cor_borda_caixa" id="cor_borda_caixa_val" value="{{ cor_borda_caixa }}">
                            <div class="color-picker-wrapper">
                                <button type="button" class="color-btn" style="background:#000000;" onclick="definirCor('cor_borda_caixa_val', '#000000')"></button>
                                <button type="button" class="color-btn" style="background:#ffffff;" onclick="definirCor('cor_borda_caixa_val', '#ffffff')"></button>
                                <input type="color" class="custom-color-input" value="{{ cor_borda_caixa }}" onchange="definirCor('cor_borda_caixa_val', this.value)">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ABA 4: Título -->
                <div id="aba4" class="tab-content">
                    <div class="form-group">
                        <label>Título da Figura (Opcional):</label>
                        <input type="text" name="titulo_prancha" value="{{ titulo_prancha }}" placeholder="Ex: Relatório Técnico">
                    </div>
                    <div class="form-group">
                        <label>Alinhamento do Título:</label>
                        <select name="titulo_alinhamento">
                            <option value="centro" {% if titulo_alinhamento == 'centro' %}selected{% endif %}>Centralizado</option>
                            <option value="esquerda" {% if titulo_alinhamento == 'esquerda' %}selected{% endif %}>Esquerda</option>
                            <option value="direita" {% if titulo_alinhamento == 'direita' %}selected{% endif %}>Direita</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Família da Fonte do Título:</label>
                        <select name="titulo_fonte_familia">
                            <option value="arial" {% if titulo_fonte_familia == 'arial' %}selected{% endif %}>Arial</option>
                            <option value="times" {% if titulo_fonte_familia == 'times' %}selected{% endif %}>Times New Roman</option>
                            <option value="cour" {% if titulo_fonte_familia == 'cour' %}selected{% endif %}>Courier New</option>
                            <option value="calibri" {% if titulo_fonte_familia == 'calibri' %}selected{% endif %}>Calibri</option>
                            <option value="aptos" {% if titulo_fonte_familia == 'aptos' %}selected{% endif %}>Aptos</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Estilo da Fonte do Título:</label>
                        <select name="titulo_fonte_estilo">
                            <option value="normal" {% if titulo_fonte_estilo == 'normal' %}selected{% endif %}>Normal</option>
                            <option value="bold" {% if titulo_fonte_estilo == 'bold' %}selected{% endif %}>Negrito</option>
                            <option value="italic" {% if titulo_fonte_estilo == 'italic' %}selected{% endif %}>Itálico</option>
                            <option value="bolditalic" {% if titulo_fonte_estilo == 'bolditalic' %}selected{% endif %}>Negrito e Itálico</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Tamanho da Fonte do Título (px):</label>
                        <input type="number" name="titulo_tamanho" value="{{ titulo_tamanho }}" min="12" max="72">
                    </div>
                    <div class="form-group">
                        <label>Cor do Título:</label>
                        <input type="hidden" name="titulo_cor" id="titulo_cor_val" value="{{ titulo_cor }}">
                        <div class="color-picker-wrapper">
                            <button type="button" class="color-btn" style="background:#000000;" onclick="definirCor('titulo_cor_val', '#000000')"></button>
                            <button type="button" class="color-btn" style="background:#ffffff;" onclick="definirCor('titulo_cor_val', '#ffffff')"></button>
                            <input type="color" class="custom-color-input" value="{{ titulo_cor }}" onchange="definirCor('titulo_cor_val', this.value)">
                        </div>
                    </div>
                </div>
            </form>
        </div>

        <div class="panel-preview">
            <h3>Pré-visualização</h3>
            <div id="container-preview">
                {% if imagem_preview %}
                    <img src="data:image/jpeg;base64,{{ imagem_preview }}" alt="Preview" class="preview-img">
                    <br>
                    <div class="export-box">
                        <label for="resolucao_dpi"><strong>Resolução de Exportação:</strong></label>
                        <select id="resolucao_dpi" form="form-prancha" name="resolucao_dpi">
                            <option value="150">150 DPI (Boa qualidade / Leve)</option>
                            <option value="300" {% if resolucao_dpi == 300 %}selected{% endif %}>300 DPI (Padrão / Alta qualidade)</option>
                            <option value="600">600 DPI (Qualidade máxima / Impressão)</option>
                        </select>
                        <button type="submit" form="form-prancha" formaction="/baixar" class="btn-success">Baixar Figura Pronta</button>
                    </div>
                {% else %}
                    <div class="aviso-vazio">Selecione as imagens na Aba 1 para gerar a pré-visualização.</div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

def gerar_rotulo(indice, estilo):
    if estilo == '1':
        return chr(65 + indice) if indice < 26 else f"A{indice-25}"
    elif estilo == '2':
        return chr(97 + indice) if indice < 26 else f"a{indice-25}"
    elif estilo == '3':
        romanos = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv']
        return romanos[indice] if indice < len(romanos) else str(indice + 1)
    elif estilo == '4':
        return str(indice + 1)
    return ""

def hex_para_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def obter_fonte(familia, estilo_fonte, tamanho):
    fontes_map = {
        'arial': {'normal': 'arial.ttf', 'bold': 'arialbd.ttf', 'italic': 'ariali.ttf', 'bolditalic': 'arialbi.ttf'},
        'times': {'normal': 'times.ttf', 'bold': 'timesbd.ttf', 'italic': 'timesi.ttf', 'bolditalic': 'timesbi.ttf'},
        'cour': {'normal': 'cour.ttf', 'bold': 'courbd.ttf', 'italic': 'couri.ttf', 'bolditalic': 'courbi.ttf'},
        'calibri': {'normal': 'calibri.ttf', 'bold': 'calibrib.ttf', 'italic': 'calibrii.ttf', 'bolditalic': 'calibriz.ttf'},
        'aptos': {'normal': 'aptos.ttf', 'bold': 'aptosb.ttf', 'italic': 'aptosi.ttf', 'bolditalic': 'aptosbi.ttf'}
    }
    familia_escolhida = fontes_map.get(familia, fontes_map['arial'])
    arquivo_fonte = familia_escolhida.get(estilo_fonte, familia_escolhida['normal'])
    try:
        return ImageFont.truetype(arquivo_fonte, size=tamanho)
    except IOError:
        try:
            return ImageFont.truetype("arial.ttf", size=tamanho)
        except IOError:
            return ImageFont.load_default()

def processar_prancha(request_form, request_files, resolucao_dpi_override=None):
    global ARQUIVOS_MEMORIA
    
    titulo_prancha = request_form.get('titulo_prancha', '').strip()
    titulo_alinhamento = request_form.get('titulo_alinhamento', 'centro')
    titulo_fonte_familia = request_form.get('titulo_fonte_familia', 'arial')
    titulo_fonte_estilo = request_form.get('titulo_fonte_estilo', 'normal')
    titulo_tamanho_base = int(request_form.get('titulo_tamanho', 32))
    titulo_cor = request_form.get('titulo_cor', '#000000')

    cols = int(request_form.get('cols', 2))
    rows = int(request_form.get('rows', 2))
    modo_tamanho_foto = request_form.get('modo_tamanho_foto', 'original')
    
    largura_quadro_cm = float(request_form.get('largura_quadro_cm', 10.0))
    altura_quadro_cm = float(request_form.get('altura_quadro_cm', 7.5))
    ajuste_por = request_form.get('ajuste_por', 'conter_sem_cortes')
    
    gap_base = int(request_form.get('gap', 15))
    cor_fundo = request_form.get('cor_fundo', '#ffffff')
    usar_quadro = request_form.get('usar_quadro', 'sim')
    borda_foto_base = int(request_form.get('borda_foto', 2))
    cor_quadro = request_form.get('cor_quadro', '#000000')
    
    estilo = request_form.get('estilo', '2')
    posicao = request_form.get('posicao', 'sup_esq')
    fonte_familia = request_form.get('fonte_familia', 'arial')
    fonte_estilo = request_form.get('fonte_estilo', 'normal')
    tamanho_fonte_legenda_base = int(request_form.get('tamanho_fonte_legenda', 36))
    cor_texto = request_form.get('cor_texto', '#000000')
    usar_caixa_legenda = request_form.get('usar_caixa_legenda', 'sim')
    formato_caixa = request_form.get('formato_caixa', 'circulo')
    cor_fundo_caixa = request_form.get('cor_fundo_caixa', '#ffffff')
    usar_borda_caixa = request_form.get('usar_borda_caixa', 'sim')
    cor_borda_caixa = request_form.get('cor_borda_caixa', '#000000')
    
    max_imagens = cols * rows
    
    ordem_str = request_form.get('ordem_indices', '')
    try:
        ordem_indices = json.loads(ordem_str) if ordem_str else list(range(len(ARQUIVOS_MEMORIA)))
    except:
        ordem_indices = list(range(len(ARQUIVOS_MEMORIA)))

    if len(ordem_indices) != len(ARQUIVOS_MEMORIA):
        ordem_indices = list(range(len(ARQUIVOS_MEMORIA)))

    indices_usados = ordem_indices[:max_imagens]
    
    if not indices_usados or not ARQUIVOS_MEMORIA:
        return None, "figura.jpg"

    dpi_atual = int(resolucao_dpi_override or request_form.get('resolucao_dpi', 300))
    fator_escala = dpi_atual / 300.0

    pixels_por_cm_atual = (dpi_atual / 2.54)
    largura_quadro_custom = int(largura_quadro_cm * pixels_por_cm_atual)
    altura_quadro_custom = int(altura_quadro_cm * pixels_por_cm_atual)

    gap = int(round(gap_base * fator_escala))
    borda_foto = int(round(borda_foto_base * fator_escala))
    tamanho_fonte_legenda = int(round(tamanho_fonte_legenda_base * fator_escala))
    titulo_tamanho = int(round(titulo_tamanho_base * fator_escala))

    imagens_processadas = []
    
    for novo_idx, original_idx in enumerate(indices_usados):
        if original_idx >= len(ARQUIVOS_MEMORIA):
            continue
        b_img = ARQUIVOS_MEMORIA[original_idx]
        img = Image.open(io.BytesIO(b_img))
        
        if modo_tamanho_foto == 'personalizado':
            if ajuste_por == 'preencher_com_cortes':
                img_obj = ImageOps.fit(img, (largura_quadro_custom, altura_quadro_custom), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                w_red, h_red = largura_quadro_custom, altura_quadro_custom
            elif ajuste_por == 'largura':
                w_orig, h_orig = img.size
                h_red = int(h_orig * (largura_quadro_custom / float(w_orig)))
                w_red = largura_quadro_custom
                img_obj = img.resize((w_red, h_red), Image.Resampling.LANCZOS)
            elif ajuste_por == 'altura':
                w_orig, h_orig = img.size
                w_red = int(w_orig * (altura_quadro_custom / float(h_orig)))
                h_red = altura_quadro_custom
                img_obj = img.resize((w_red, h_red), Image.Resampling.LANCZOS)
            else:  # conter_sem_cortes
                w_orig, h_orig = img.size
                fator = min(largura_quadro_custom / float(w_orig), altura_quadro_custom / float(h_orig))
                w_red = int(w_orig * fator)
                h_red = int(h_orig * fator)
                img_red = img.resize((w_red, h_red), Image.Resampling.LANCZOS)
                
                cor_fundo_rgb = hex_para_rgb(cor_fundo)
                img_obj = Image.new('RGB', (largura_quadro_custom, altura_quadro_custom), color=cor_fundo_rgb)
                x_paste = (largura_quadro_custom - w_red) // 2
                y_paste = (altura_quadro_custom - h_red) // 2
                img_obj.paste(img_red, (x_paste, y_paste))
                w_red, h_red = largura_quadro_custom, altura_quadro_custom
        else:
            w_orig, h_orig = img.size
            largura_max_padrao = int(700 * fator_escala)
            fator = largura_max_padrao / float(w_orig)
            w_red = largura_max_padrao
            h_red = int(h_orig * fator)
            img_obj = img.resize((w_red, h_red), Image.Resampling.LANCZOS)
            
        imagens_processadas.append({'img': img_obj, 'w': w_red, 'h': h_red, 'idx': original_idx})
    
    if not imagens_processadas:
        return None, "figura.jpg"

    alturas_linhas = [0] * rows
    larguras_colunas = [0] * cols
    
    for idx, info in enumerate(imagens_processadas):
        c = idx % cols
        r = idx // cols
        if info['h'] > alturas_linhas[r]:
            alturas_linhas[r] = info['h']
        if info['w'] > larguras_colunas[c]:
            larguras_colunas[c] = info['w']
    
    largura_celula = max(larguras_colunas) if larguras_colunas else int(700 * fator_escala)
    largura_total = (cols * largura_celula) + ((cols + 1) * gap)
    
    fonte_titulo = obter_fonte(titulo_fonte_familia, titulo_fonte_estilo, tamanho=titulo_tamanho)
    temp_img_dummy = Image.new('RGB', (10, 10))
    draw_dummy = ImageDraw.Draw(temp_img_dummy)
    
    altura_cabecalho = 0
    if titulo_prancha:
        bbox_t = draw_dummy.textbbox((0, 0), titulo_prancha, font=fonte_titulo)
        altura_t_real = bbox_t[3] - bbox_t[1]
        altura_cabecalho = altura_t_real + int(30 * fator_escala)

    altura_total = altura_cabecalho + sum(alturas_linhas) + ((rows + 1) * gap)
    
    cor_fundo_rgb = hex_para_rgb(cor_fundo)
    cor_quadro_rgb = hex_para_rgb(cor_quadro)
    cor_texto_rgb = hex_para_rgb(cor_texto)
    cor_fundo_caixa_rgb = hex_para_rgb(cor_fundo_caixa)
    cor_borda_caixa_rgb = hex_para_rgb(cor_borda_caixa)
    titulo_cor_rgb = hex_para_rgb(titulo_cor)
    
    prancha = Image.new('RGB', (largura_total, altura_total), color=cor_fundo_rgb)
    draw_prancha = ImageDraw.Draw(prancha)
    
    fonte_legenda = obter_fonte(fonte_familia, fonte_estilo, tamanho=tamanho_fonte_legenda)
        
    if titulo_prancha:
        bbox_t = draw_prancha.textbbox((0, 0), titulo_prancha, font=fonte_titulo)
        largura_t = bbox_t[2] - bbox_t[0]
        
        if titulo_alinhamento == 'esquerda':
            x_t = gap + int(10 * fator_escala)
        elif titulo_alinhamento == 'direita':
            x_t = largura_total - largura_t - gap - int(10 * fator_escala)
        else:
            x_t = (largura_total - largura_t) // 2
            
        y_t = gap + (altura_cabecalho - (bbox_t[3] - bbox_t[1])) // 2 - bbox_t[1]
        draw_prancha.text((x_t, y_t), titulo_prancha, fill=titulo_cor_rgb, font=fonte_titulo)

    pos_y_linhas = []
    y_atual = gap + altura_cabecalho
    for altura_linha in alturas_linhas:
        pos_y_linhas.append(y_atual)
        y_atual += altura_linha + gap

    for idx, info in enumerate(imagens_processadas):
        c = idx % cols
        r = idx // cols
        
        w_img = info['w']
        h_img = info['h']
        
        x_celula = gap + (c * (largura_celula + gap))
        x_img = x_celula + (largura_celula - w_img) // 2
        y_img = pos_y_linhas[r]
        
        prancha.paste(info['img'], (x_img, y_img))
        
        if usar_quadro == 'sim' and borda_foto > 0:
            for b in range(borda_foto):
                draw_prancha.rectangle(
                    [x_img - b, y_img - b, x_img + w_img - 1 + b, y_img + h_img - 1 + b],
                    outline=cor_quadro_rgb
                )
        
        if estilo in ['1', '2', '3', '4']:
            texto = gerar_rotulo(idx, estilo)
            padding = max(4, int(tamanho_fonte_legenda * 0.25))
            bbox = draw_prancha.textbbox((0, 0), texto, font=fonte_legenda)
            largura_texto = bbox[2] - bbox[0]
            altura_texto = bbox[3] - bbox[1]
            
            margin_h = int(15 * fator_escala) + (borda_foto if usar_quadro == 'sim' else 0)
            margin_v = int(15 * fator_escala) + (borda_foto if usar_quadro == 'sim' else 0)
            
            if posicao == 'sup_esq':
                pos_x = x_img + margin_h
                pos_y = y_img + margin_v
            elif posicao == 'sup_dir':
                pos_x = x_img + w_img - largura_texto - (padding * 2) - margin_h
                pos_y = y_img + margin_v
            elif posicao == 'inf_esq':
                pos_x = x_img + margin_h
                pos_y = y_img + h_img - altura_texto - (padding * 2) - margin_v
            else:
                pos_x = x_img + w_img - largura_texto - (padding * 2) - margin_h
                pos_y = y_img + h_img - altura_texto - (padding * 2) - margin_v
            
            if usar_caixa_legenda == 'sim':
                caixa_largura = largura_texto + (padding * 2)
                caixa_altura = altura_texto + (padding * 2)
                caixa_box = [pos_x, pos_y, pos_x + caixa_largura, pos_y + caixa_altura]
                
                raio_arredondado = int(12 * fator_escala)
                if formato_caixa == 'circulo':
                    draw_prancha.ellipse(caixa_box, fill=cor_fundo_caixa_rgb, outline=cor_borda_caixa_rgb if usar_borda_caixa == 'sim' else None)
                elif formato_caixa == 'arredondado':
                    draw_prancha.rounded_rectangle(caixa_box, radius=raio_arredondado, fill=cor_fundo_caixa_rgb, outline=cor_borda_caixa_rgb if usar_borda_caixa == 'sim' else None)
                else:
                    draw_prancha.rectangle(caixa_box, fill=cor_fundo_caixa_rgb, outline=cor_borda_caixa_rgb if usar_borda_caixa == 'sim' else None)
                    
                x_texto = pos_x + (caixa_largura - largura_texto) // 2 - bbox[0]
                y_texto = pos_y + (caixa_altura - altura_texto) // 2 - bbox[1]
                draw_prancha.text((x_texto, y_texto), texto, fill=cor_texto_rgb, font=fonte_legenda)
            else:
                draw_prancha.text((pos_x - bbox[0], pos_y - bbox[1]), texto, fill=cor_texto_rgb, font=fonte_legenda)
                
    nome_arquivo = f"figura_{cols}x{rows}_{dpi_atual}dpi.jpg"
    return prancha, nome_arquivo

@app.route('/logo.png')
def logo():
    return send_from_directory(os.getcwd(), 'logo.png')

@app.route('/', methods=['GET', 'POST'])
def index():
    global ARQUIVOS_MEMORIA, Nomes_Arquivos_Memoria
    
    if request.method == 'POST':
        arquivos_enviados = request.files.getlist('imagens')
        if arquivos_enviados and arquivos_envinados[0].filename != '':
            pass # Tratado abaixo
        if arquivos_enviados:
            validos = [arq for arq in arquivos_enviados if arq.filename != '']
            if validos:
                ARQUIVOS_MEMORIA = [arq.read() for arq in validos]
                Nomes_Arquivos_Memoria = [arq.filename for arq in validos]

    titulo_prancha = request.form.get('titulo_prancha', '').strip() if request.method == 'POST' else ""
    titulo_alinhamento = request.form.get('titulo_alinhamento', 'centro') if request.method == 'POST' else "centro"
    titulo_fonte_familia = request.form.get('titulo_fonte_familia', 'arial') if request.method == 'POST' else "arial"
    titulo_fonte_estilo = request.form.get('titulo_fonte_estilo', 'normal') if request.method == 'POST' else "normal"
    titulo_tamanho = int(request.form.get('titulo_tamanho', 32)) if request.method == 'POST' else 32
    titulo_cor = request.form.get('titulo_cor', '#000000') if request.method == 'POST' else "#000000"

    cols = int(request.form.get('cols', 2)) if request.method == 'POST' else 2
    rows = int(request.form.get('rows', 2)) if request.method == 'POST' else 2
    modo_tamanho_foto = request.form.get('modo_tamanho_foto', 'original') if request.method == 'POST' else "original"
    
    largura_quadro_cm = float(request.form.get('largura_quadro_cm', 10.0)) if request.method == 'POST' else 10.0
    altura_quadro_cm = float(request.form.get('altura_quadro_cm', 7.5)) if request.method == 'POST' else 7.5
    ajuste_por = request.form.get('ajuste_por', 'conter_sem_cortes') if request.method == 'POST' else "conter_sem_cortes"

    gap = int(request.form.get('gap', 15)) if request.method == 'POST' else 15
    cor_fundo = request.form.get('cor_fundo', '#ffffff') if request.method == 'POST' else "#ffffff"
    usar_quadro = request.form.get('usar_quadro', 'sim') if request.method == 'POST' else "sim"
    borda_foto = int(request.form.get('borda_foto', 2)) if request.method == 'POST' else 2
    cor_quadro = request.form.get('cor_quadro', '#000000') if request.method == 'POST' else "#000000"
    
    estilo = request.form.get('estilo', '2') if request.method == 'POST' else "2"
    posicao = request.form.get('posicao', 'sup_esq') if request.method == 'POST' else "sup_esq"
    fonte_familia = request.form.get('fonte_familia', 'arial') if request.method == 'POST' else "arial"
    fonte_estilo = request.form.get('fonte_estilo', 'normal') if request.method == 'POST' else "normal"
    tamanho_fonte_legenda = int(request.form.get('tamanho_fonte_legenda', 36)) if request.method == 'POST' else 36
    cor_texto = request.form.get('cor_texto', '#000000') if request.method == 'POST' else "#000000"
    usar_caixa_legenda = request.form.get('usar_caixa_legenda', 'sim') if request.method == 'POST' else "sim"
    formato_caixa = request.form.get('formato_caixa', 'circulo') if request.method == 'POST' else "circulo"
    cor_fundo_caixa = request.form.get('cor_fundo_caixa', '#ffffff') if request.method == 'POST' else "#ffffff"
    usar_borda_caixa = request.form.get('usar_borda_caixa', 'sim') if request.method == 'POST' else "sim"
    cor_borda_caixa = request.form.get('cor_borda_caixa', '#000000') if request.method == 'POST' else "#000000"
    resolucao_dpi = int(request.form.get('resolucao_dpi', 300)) if request.method == 'POST' else 300

    ordem_str = request.form.get('ordem_indices', '') if request.method == 'POST' else ''
    try:
        ordem_indices = json.loads(ordem_str) if ordem_str else list(range(len(ARQUIVOS_MEMORIA)))
    except:
        ordem_indices = list(range(len(ARQUIVOS_MEMORIA)))

    if len(ordem_indices) != len(ARQUIVOS_MEMORIA):
        ordem_indices = list(range(len(ARQUIVOS_MEMORIA)))

    imagem_preview = None
    nome_arquivo = f"figura_{cols}x{rows}.jpg"
    
    if request.method == 'POST':
        prancha, nome_arquivo = processar_prancha(request.form, request.files, resolucao_dpi_override=300)
        if prancha:
            buffered = io.BytesIO()
            prancha.save(buffered, format="JPEG", quality=90)
            imagem_preview = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return render_template_string(HTML_TEMPLATE, 
                                  imagem_preview=imagem_preview,
                                  nome_arquivo=nome_arquivo, 
                                  total_imagens=len(ARQUIVOS_MEMORIA),
                                  nomes_arquivos=Nomes_Arquivos_Memoria,
                                  ordem_indices=ordem_indices,
                                  ordem_indices_json=json.dumps(ordem_indices),
                                  titulo_prancha=titulo_prancha,
                                  titulo_alinhamento=titulo_alinhamento,
                                  titulo_fonte_familia=titulo_fonte_familia,
                                  titulo_fonte_estilo=titulo_fonte_estilo,
                                  titulo_tamanho=titulo_tamanho,
                                  titulo_cor=titulo_cor,
                                  cols=cols,
                                  rows=rows,
                                  modo_tamanho_foto=modo_tamanho_foto,
                                  largura_quadro_cm=largura_quadro_cm,
                                  altura_quadro_cm=altura_quadro_cm,
                                  ajuste_por=ajuste_por,
                                  gap=gap,
                                  cor_fundo=cor_fundo,
                                  usar_quadro=usar_quadro,
                                  borda_foto=borda_foto,
                                  cor_quadro=cor_quadro,
                                  estilo=estilo,
                                  posicao=posicao,
                                  fonte_familia=fonte_familia,
                                  fonte_estilo=fonte_estilo,
                                  tamanho_fonte_legenda=tamanho_fonte_legenda,
                                  cor_texto=cor_texto,
                                  usar_caixa_legenda=usar_caixa_legenda,
                                  formato_caixa=formato_caixa,
                                  cor_fundo_caixa=cor_fundo_caixa,
                                  usar_borda_caixa=usar_borda_caixa,
                                  cor_borda_caixa=cor_borda_caixa,
                                  resolucao_dpi=resolucao_dpi)

@app.route('/baixar', methods=['POST'])
def baixar():
    prancha, nome_arquivo = processar_prancha(request.form, request.files)
    if not prancha:
        return "Nenhuma imagem para exportar.", 400
    
    caminho_saida = os.path.join(PASTA_SAIDA, nome_arquivo)
    prancha.save(caminho_saida, quality=98)
    return send_from_directory(PASTA_SAIDA, nome_arquivo, as_attachment=True)

def abrir_navegador():
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, abrir_navegador).start()
    app.run(debug=False, port=5000)