O Mecanix é um sistema web desenvolvido com o objetivo de facilitar o gerenciamento de oficinas mecânicas. A aplicação permite organizar as informações dos clientes e de seus veículos, cadastrar peças e serviços, registrar ordens de serviço e acompanhar o andamento dos atendimentos. Também oferece recursos para consultar o histórico de serviços, visualizar relatórios de serviços e faturamento e gerenciar os usuários do sistema.

O sistema possui uma tela de login para controlar o acesso e diferentes níveis de permissão, de acordo com o perfil de cada usuário. Sua interface foi desenvolvida para facilitar a utilização e tornar as atividades do dia a dia mais organizadas.

O desenvolvimento foi realizado utilizando Python e Flask no backend, SQLite para o armazenamento dos dados e HTML, CSS e JavaScript na construção da interface. Também foi utilizado o Jinja2 para integrar as páginas ao funcionamento da aplicação.

Como executar o projeto?

Para executar o Mecanix em um computador pessoal, é necessário ter o Python instalado, além do Git e do gerenciador de pacotes pip.

Primeiramente, clone o repositório do projeto utilizando o comando git clone https://github.com/Brunodevei/Mecanix

Em seguida, entre na pasta do projeto utilizando o comando cd mecanix.

Para acessar a versão correspondente à Iteração 2, identificada pela tag v2, execute o comando git checkout v2.

Depois, crie um ambiente virtual para instalar as dependências do projeto utilizando o comando python -m venv venv.

Ative o ambiente virtual. No Windows, execute venv\Scripts\activate. No Linux ou macOS, utilize source venv/bin/activate.

Com o ambiente virtual ativado, instale as dependências necessárias utilizando o comando pip install -r requirements.txt.

Antes de iniciar a aplicação, configure a senha inicial do administrador por meio da variável de ambiente ADMIN_INITIAL_PASSWORD. No Windows, utilizando o Prompt de Comando, execute set ADMIN_INITIAL_PASSWORD=sua_senha. No PowerShell, utilize $env="sua_senha". No Linux ou macOS, utilize export ADMIN_INITIAL_PASSWORD="sua_senha".

Por fim, inicie a aplicação executando python app.py.

Após a inicialização, abra o navegador e acesse o endereço http://127.0.0.1:5000 para utilizar o sistema.

O banco de dados SQLite é inicializado automaticamente pela aplicação. Caso a senha inicial do administrador não seja configurada pela variável de ambiente, o sistema gera uma senha automaticamente e a apresenta no terminal durante a inicialização.