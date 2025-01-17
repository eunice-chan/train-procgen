# CS 182 RL Project
TODO Add summary

## Setup
We recommend running the code in the provided notebook `fruitbot.ipynb` on Google Colab, as CMake is required.

To run locally:
```
pip install https://github.com/openai/baselines/archive/9ee399f5b20cd70ac0a871927a6cf043b478193f.zip
pip install -r requirements.txt
```

Install a version of ProcGen that allows environments to be reset:
```
git clone https://github.com/minqi/procgen.git train-procgen/train_procgen/procgen_replay
python train-procgen/train_procgen/procgen_replay/setup.py install
```

# Train
## Baseline
50 training levels:
```
python train_procgen/train.py --env_name fruitbot --distribution_mode easy --num_levels 50 --start_level 500 --timesteps_per_proc 5_000_000 --log_dir [LOG_DIR]
```

## Prioritized Level Replay
`--level_sampler_strategy` = ['value_l1', 'policy_entropy', 'rnd']

`--score_transform` = ['rank', 'softmax']

`--save_dir` = directory to save model and logs in the `models/` and `logs/` subdirectories respectively

`--model_name` = model and logs will be stored in `[SAVE_DIR]/models/[MODEL_NAME]` and `[SAVE_DIR]/logs/[MODEL_NAME]/progress.csv` respectively

```
python train-procgen/train_procgen/train_plr.py --timesteps_per_proc 5_000_000 --level_sampler_strategy policy_entropy --score_transform softmax --model_name entropy_softmax_fixed --save_dir [SAVE_DIR]
```

## Mixreg
`--mix_mode` = ['nomix', 'mixreg']

`--save_dir` = directory to save model and logs
```
python train-procgen/train_procgen/train_mixreg.py --env_name fruitbot --distribution_mode easy --num_levels 50 --start_level 500 --mix_mode mixreg --timesteps_per_proc 5_000_000 --save_dir [SAVE_DIR]
```

## Augmix
`--mixture_width` = Number of augmentation chains to mix per augmented example
`--mixture_depth` = Depth of augmentation chains. -1 denotes stochastic depth in [1, 3]
`--aug_severity` = Severity of base augmentation operators
`--aug_prob_coeff` = Probability distribution coefficients
`--autoaug_policy_idx` = model choice of 0, 1, 2 (0:ImageNetPolicy 1:CIFAR10Policy 2:SVHNPolicy)
```
python -m train_procgen.train --env_name fruitbot --distribution_mode easy --num_levels 50 --start_level 1850 --timesteps_per_proc 5_000_000 --do_eval --do_test 
--log_dir "/log" --alternate_ppo --do_aug --autoaugment --autoaug_policy_idx 2
```

## Prioritized Level Replay + Mixreg
`--level_sampler_strategy` = ['value_l1', 'policy_entropy', 'rnd']

`--score_transform` = ['rank', 'softmax']

`--mix_mode` = ['nomix', 'mixreg']

`--save_dir` = directory to save model and logs
```
python train-procgen/train_procgen/train_mixreg_plr.py --env_name fruitbot --distribution_mode easy --num_levels 100 --start_level 500 --mix_mode mixreg --level_sampler_strategy value_l1 --score_transform rank --timesteps_per_proc 5_000_000 --save_dir [SAVE_DIR]
```

# Evaluate
`--log_dir` = path to save evaluation results

`--load_model` = path to model

`--num_trials` = number of trials to evaluate the model
```
python train-procgen/train_procgen/evaluate.py --env_name fruitbot --distribution_mode easy --num_levels 500 --start_level 0 --num_trials 1 --log_dir [LOG_DIR] --load_model [MODEL_PATH]
```
