echo "Cloning Repo...."
if [ -z $BRANCH ]
then
  echo "Cloning main branch...."
  git clone https://github.com/SakirBey1/GrupMüzikBotu /GrupMüzikBotu
else
  echo "Cloning $BRANCH branch...."
  git clone https://github.com/SakirBey1/GrupMüzikBotu -b $BRANCH /GrupMüzikBotu
fi
cd /GrupMüzikBotu
pip3 install -U -r requirements.txt
echo "Starting Bot...."
python3 main.py
