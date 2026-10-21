document.addEventListener("DOMContentLoaded", function() {
    const volante = document.getElementById("volante");
    const contador = document.getElementById("contagem");
    const btnConfirmar = document.getElementById("btn-confirmar");
    const btnSurpresinha = document.getElementById("btn-surpresinha");
    const labelNome = document.getElementById("nome-jogador");
    const labelSaldo = document.getElementById("saldo-valor");

    // LER O CPF LOGADO DA MEMÓRIA: Se não houver ninguém, usa o teste como plano B
    const CPF_LOGADO = localStorage.getItem("usuario_cpf") || "12345678909"; 
    const RODADA_TESTE = 1;

    let dezenasSelecionadas = [];

    // 1. CARREGAR DADOS REAIS DO JOGADOR NO TOPO DA TELA
    if (CPF_LOGADO === "12345678909") {
        labelNome.innerText = "Jogador de Teste";
    } else {
        labelNome.innerText = "Sua Conta Nova";
    }
    
    // Busca o saldo do CPF correto direto no banco de dados do Python
    fetch("/api/carteira/saldo/" + CPF_LOGADO)
        .then(res => res.json())
        .then(dados => {
            if (dados.sucesso) {
                labelSaldo.innerText = "R$ " + dados.saldo.toFixed(2).replace('.', ',');
            }
        })
        .catch(err => console.log("Erro de conexão com a API de saldo: ", err));

    // 2. GERAR AS 60 BOLINHAS DO VOLANTE NA TELA
    for (let i = 1; i <= 60; i++) {
        let numeroFormatado = i < 10 ? "0" + i : i;
        let botao = document.createElement("button");
        botao.innerText = numeroFormatado;
        botao.classList.add("num-dezena");
        botao.dataset.numero = i;

        botao.addEventListener("click", () => alternarSelecaoDezena(botao, i));
        volante.appendChild(botao);
    }

    // 3. LOGICA DO CLIQUE NAS BOLINHAS
    function alternarSelecaoDezena(botao, numero) {
        if (dezenasSelecionadas.includes(numero)) {
            dezenasSelecionadas = dezenasSelecionadas.filter(n => n !== numero);
            botao.classList.remove("selecionado");
        } else {
            if (dezenasSelecionadas.length >= 6) {
                alert("Você já escolheu as 6 dezenas do seu jogo!");
                return;
            }
            dezenasSelecionadas.push(numero);
            botao.classList.add("selecionado");
        }

        contador.innerText = dezenasSelecionadas.length;

        if (dezenasSelecionadas.length === 6) {
            btnConfirmar.disabled = false;
            btnConfirmar.classList.add("ativo");
        } else {
            btnConfirmar.disabled = true;
            btnConfirmar.classList.remove("ativo");
        }
    }

    // 4. LOGICA DO BOTAO SURPRESINHA
    btnSurpresinha.addEventListener("click", () => {
        dezenasSelecionadas = [];
        document.querySelectorAll(".num-dezena").forEach(b => b.classList.remove("selecionado"));

        while (dezenasSelecionadas.length < 6) {
            let numAleatorio = Math.floor(Math.random() * 60) + 1;
            if (!dezenasSelecionadas.includes(numAleatorio)) {
                dezenasSelecionadas.push(numAleatorio);
                let botao = document.querySelector("[data-numero='" + numAleatorio + "']");
                if (botao) botao.classList.add("selecionado");
            }
        }
        contador.innerText = 6;
        btnConfirmar.disabled = false;
        btnConfirmar.classList.add("ativo");
    });

    // 5. ENVIAR AS DEZENAS PARA O PYTHON GRAVAR O JOGO
    btnConfirmar.addEventListener("click", () => {
        if (dezenasSelecionadas.length !== 6) return;

        const dadosFormulario = {
            cpf: CPF_LOGADO, // Envia as dezenas vinculadas ao CPF de quem está logado de verdade!
            dezenas: dezenasSelecionadas,
            id_rodada: RODADA_TESTE
        };

        fetch("/api/jogos/comprar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dadosFormulario)
        })
        .then(res => res.json())
        .then(resposta => {
            if (resposta.mensagem) {
                alert("🎉 " + resposta.mensagem);
                dezenasSelecionadas = [];
                document.querySelectorAll(".num-dezena").forEach(b => b.classList.remove("selecionado"));
                contador.innerText = 0;
                btnConfirmar.disabled = true;
                btnConfirmar.classList.remove("ativo");
                window.location.reload();
            } else {
                alert("❌ Erro: " + (resposta.detail || resposta.erro));
            }
        })
        .catch(err => alert("Erro ao conectar com o servidor do app."));
    });
});
